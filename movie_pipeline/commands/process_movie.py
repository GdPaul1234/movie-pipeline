import concurrent.futures
import itertools
import logging
from collections import deque
from pathlib import Path
from typing import cast

import binpacking
import ffmpeg
import yaml
from rich import print
from rich.live import Live
from rich.progress import Progress
from rich.tree import Tree
from schema import Optional, Regex, Schema

from util import diff_tracking, position_in_seconds

from ..lib.backup_policy_executor import BackupPolicyExecutor, EdlFile
from ..lib.ffmpeg_with_progress import ffmpeg_command_with_progress
from ..lib.movie_path_destination_finder import MoviePathDestinationFinder
from ..lib.ui_factory import (ProgressListener, ProgressUIFactory, transient_task_progress)
from ..models.movie_file import LegacyMovieFile
from ..models.movie_segments import MovieSegments

logger = logging.getLogger(__name__)

edl_content_schema = Schema({
    # valid filename of the output file with .mp4 suffix
    "filename": Regex(r"^[\w&àéèï'!(), -.]+\.mp4$"),
    # format: hh:mm:ss.ss-hh:mm:ss.ss,hh-mm:ss…
    "segments": Regex(r'(?:(?:\d{2}:\d{2}:\d{2}\.\d{2,3})-(?:\d{2}:\d{2}:\d{2}\.\d{2,3}),)+'),
    Optional("skip_backup", default=False): bool
})


class MovieFileProcessor:
    def __init__(
        self,
        edl_path: Path,
        progress: Progress,
        config,
        *,
        backup_policy_executor=BackupPolicyExecutor
    ) -> None:
        """
        Args:
            edl_path (Path): path to edit decision list file
                (naming: {movie file with suffix}.txt)
        """
        edl_content = yaml.safe_load(edl_path.read_text(encoding='utf-8'))
        edl_content = edl_content_schema.validate(edl_content)
        self._edl_file = EdlFile(edl_path, edl_content)

        self._progress = progress
        self._backup_policy_executor = backup_policy_executor(self._edl_file, config)

        self._movie_segments = MovieSegments(raw_segments=self._edl_file.content['segments'])
        self._segments = self._movie_segments.segments
        self._config = config

    def process(self):
        deque(self.process_with_progress(), maxlen=0)

    def process_with_progress(self):
        in_file_path = self._edl_file.path.with_suffix('')
        in_file = ffmpeg.input(str(in_file_path))
        probe = ffmpeg.probe(in_file_path)

        audio_streams = [stream for stream in probe['streams']
                         if stream.get('codec_type', 'N/A') == 'audio']
        nb_audio_streams = len(audio_streams)
        logger.debug(f'{nb_audio_streams=}')

        dest_filename = self._edl_file.content['filename']
        dest_path = MoviePathDestinationFinder(LegacyMovieFile(dest_filename), self._config).resolve_destination()
        dest_filepath = dest_path.joinpath(dest_filename)

        command = (
            ffmpeg
            .concat(
                *self._movie_segments.to_ffmpeg_concat_segments(in_file, audio_streams),
                v=1, a=nb_audio_streams
            )
            .output(
                str(dest_filepath),
                vcodec='h264_nvenc',
                acodec='aac', cutoff='20K', audio_bitrate='256K', ac=2,
                dn=None, sn=None, ignore_unknown=None
            )
        )

        try:
            logger.debug(f'{self._segments=}')
            logger.info('Running: %s', command.compile())

            total_seconds = self._movie_segments.total_seconds
            with transient_task_progress(self._progress, description=dest_filename, total=total_seconds) as task_id:
                for item in ffmpeg_command_with_progress(command, cmd=['ffmpeg', '-hwaccel', 'cuda']):
                    if item.get('time'):
                        processed_time = position_in_seconds(item['time'])
                        yield 0.8 * (processed_time / total_seconds)
                        self._progress.update(task_id, completed=processed_time)

            with transient_task_progress(self._progress, f'Backuping {dest_filename}...'):
                self._backup_policy_executor.execute(original_file_path=in_file_path)

            yield 1.0
            self._progress.update(task_id, completed=total_seconds)

            logger.info('"%s" processed sucessfully', dest_filepath)
        except ffmpeg.Error as e:
            logger.exception(e.stderr)
            raise e


class MovieFileProcessorFolderRunner:
    def __init__(self, folder_path: Path, edl_ext: str, progress_listener: ProgressListener, config) -> None:
        self._folder_path = folder_path
        self._edl_ext = edl_ext
        self._progress = progress_listener
        self._config = config

        self._nb_worker = self._config.getint('Processor', 'nb_worker', fallback=1)
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
            prev_edl_progress = [0.]  # mutable!

            for edl_progress in MovieFileProcessor(edl, job_progress, self._config).process_with_progress():
                with diff_tracking(prev_edl_progress, edl_progress) as diff_edl_progress:
                    job_progress.advance(task_id, advance=diff_edl_progress)
                    self._progress.overall_progress.advance(self._progress.overall_task, advance=diff_edl_progress / len(edls))

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


def command(options, config):
    logger.debug('args: %s', vars(options))

    filepath = Path(options.file)
    edl_ext: str = options.custom_ext

    try:
        if filepath.is_file() and filepath.suffix == edl_ext:
            with Progress() as progress:
                MovieFileProcessor(filepath, progress, config).process()
        elif filepath.is_dir():
            progress_listener = ProgressUIFactory.create_process_listener()
            MovieFileProcessorFolderRunner(filepath, edl_ext, progress_listener, config).process_directory()
        else:
            raise ValueError('Unknown file type')
    except Exception as e:
        logger.exception(e)
