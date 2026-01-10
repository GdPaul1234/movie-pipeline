import json
from datetime import datetime
from typing import Iterator

from pydantic import BaseModel
from pydantic.types import DirectoryPath, FilePath

from .....jobs.base_xyops_plugin import ReportedProgress
from .....lib.util import timed_run
from .....settings import Settings
from ...core import MovieFileProcessor


class FileInput(BaseModel):
    file_path: FilePath
    edl_ext: str


def process_file(input: FileInput, config: Settings) -> Iterator[ReportedProgress]:
    edl = input.file_path.with_suffix(f'{input.file_path.suffix}{input.edl_ext}')
    new_edl_name = edl.with_suffix(f'.pending_yml_{int(datetime.utcnow().timestamp())}')
    edl.rename(new_edl_name)

    movie_file_processor = MovieFileProcessor(new_edl_name, config)
    elapsed_times: dict[str, float] = {}

    for step_progress_result in movie_file_processor.movie_file_processor_root_step.process_all():
        elapsed_times[step_progress_result.current_step_name] = round(step_progress_result.current_step_elapsed_time, 2)
        yield {'xy': 1, 'progress': round(step_progress_result.total_percent, 2), 'perf': elapsed_times}


class DirectoryInput(BaseModel):
    folder_path: DirectoryPath
    edl_ext: str


def process_directory(input: DirectoryInput, config: Settings) -> Iterator[ReportedProgress]:
    def submit_actions():
        edls: list[FilePath] = []

        for edl in input.folder_path.glob(f'*{input.edl_ext}'):
            new_edl_name = edl.with_suffix(f'.pending_yml_{int(datetime.utcnow().timestamp())}')
            edl.rename(new_edl_name)
            edls.append(new_edl_name)

        process_file_inputs = [{'file_path': str(edl_path.with_suffix('')), 'edl_ext': edl_path.suffix} for edl_path in edls]
        print(json.dumps({'xy': 1, 'data': {'process_file_inputs': process_file_inputs}}))

    _, process_time = timed_run(submit_actions)
    yield {'xy': 1, 'progress': 1., 'perf': {'SubmitJobs': process_time}}
