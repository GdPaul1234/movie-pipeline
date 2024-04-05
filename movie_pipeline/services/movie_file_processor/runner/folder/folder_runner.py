import concurrent.futures
import itertools
import logging
from pathlib import Path
from typing import TypedDict, cast

import binpacking
from rich import print
from rich.live import Live
from rich.progress import Progress, TaskID
from rich.tree import Tree

from .....lib.ui_factory import ProgressListener, ProgressUIFactory
from .....lib.util import diff_tracking
from .....settings import Settings
from ...core import MovieFileProcessor
from ...movie_file_processor_step import BaseStep, StepProgressResult

logger = logging.getLogger(__name__)


class MovieFileProcessorFolderRunner:
    def __init__(self, folder_path: Path, edl_ext: str, progress_listener: ProgressListener, config: Settings) -> None:
        self._folder_path = folder_path
        self._edl_ext = edl_ext
        self._progress = progress_listener
        self._config = config

        self._nb_worker = config.Processor.nb_worker if config.Processor else 1
        self._jobs_progresses = [ProgressUIFactory.create_job_progress() for _ in range(self._nb_worker)]

    def _distribute_fairly_edl(self):
        edls = list(self._folder_path.glob(f'*{self._edl_ext}'))

        if len(edls) == 0:
            return list(itertools.repeat([], times=self._nb_worker))

        return binpacking.to_constant_bin_number(
            edls,
            N_bin=self._nb_worker,
            key=lambda f: f.with_suffix('').stat().st_size
        )

    def _prepare_processing(self, tree_logger: Tree):
        groups: list[list[Path]] = []

        for index, group in enumerate(self._distribute_fairly_edl()):
            subtree = tree_logger.add(f'Worker {index}')
            subgroup: list[Path] = []

            # rename distributed edls
            for edl in cast(list[Path], group):
                new_edl_name = edl.with_suffix(f'.pending_yml_{index}')
                edl.rename(new_edl_name)

                subgroup.append(new_edl_name)
                subtree.add(str(new_edl_name))

            groups.append(subgroup)

        return groups

    def _execute_processing(self, worker_id: int, edls: list[Path], edl_ext: str):
        job_progress = self._jobs_progresses[worker_id]
        task_id = job_progress.add_task(f'{edl_ext}...', total=len(edls))

        for edl in sorted(edls, key=lambda edl: edl.stat().st_size, reverse=True):
            movie_file_processor = MovieFileProcessor(edl, self._config)
            prev_edl_progress = [0.]  # mutable!

            for edl_progress in process_with_progress_tui(job_progress, movie_file_processor.movie_file_processor_root_step):
                with diff_tracking(prev_edl_progress, edl_progress) as diff_edl_progress:
                    job_progress.advance(task_id, advance=diff_edl_progress)
                    self._progress.overall_progress.advance(self._progress.overall_task, advance=diff_edl_progress / len(edls))

            logger.info('"%s" processed successfully', edl)

    def process_directory(self):
        logger.info('Processing: "%s"', self._folder_path)

        tree = Tree("EDL to be processed")
        edl_groups = self._prepare_processing(tree_logger=tree)
        print(tree)

        with Live(self._progress.layout, refresh_per_second=10):
            self._progress.overall_progress.update(self._progress.overall_task, total=self._nb_worker)
            ProgressUIFactory.create_job_panel_row_from_job_progress(self._progress.layout, self._jobs_progresses)

            with concurrent.futures.ThreadPoolExecutor(max_workers=self._nb_worker) as executor:
                future_tasks = {
                    executor.submit(self._execute_processing, index, group, edl_ext): edl_ext
                    for index, edl_ext, group in map(
                        lambda index: (index, f'.pending_yml_{index}', edl_groups[index]),
                        range(self._nb_worker)
                    )
                }

                for future in concurrent.futures.as_completed(future_tasks):
                    edl_ext = future_tasks[future]
                    try:
                        future.result()  # wait for completion
                    except Exception as e:
                        logger.error('Exception when processing *%s files: %s', edl_ext, e)
                    else:
                        logger.info('Processed all %s edl files', edl_ext)

        logger.info('All movie files in "%s" processed', self._folder_path)


ProgressState = TypedDict('ProgressState', {'current_step': BaseStep | None, 'task_id': TaskID | None})


def process_with_progress_tui(progress: Progress, movie_file_processor_root_step: BaseStep):
    state: ProgressState = {'current_step': None, 'task_id': None}

    def stop_previous_task():
        if state['task_id'] is None:
            return
        progress.stop_task(state['task_id'])
        progress.update(state['task_id'], visible=False)

    def add_task_if_needed(step_progress_result: StepProgressResult):
        if step_progress_result.current_step != state['current_step']:
            stop_previous_task()
            state['current_step'] = step_progress_result.current_step
            state['task_id'] = progress.add_task(description=state['current_step'].description, total=1.0)

    def update_task(step_progress_result: StepProgressResult):
        if state['task_id'] is None:
            return
        progress.update(state['task_id'], completed=step_progress_result.current_step_percent)

    for step_progress_result in movie_file_processor_root_step.process_all():
        add_task_if_needed(step_progress_result)
        update_task(step_progress_result)
        yield step_progress_result.total_percent

    stop_previous_task()
