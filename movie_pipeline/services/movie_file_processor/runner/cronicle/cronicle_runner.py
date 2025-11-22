import json
from datetime import datetime
from typing import Any, Iterator

import requests
from pydantic import BaseModel, DirectoryPath
from pydantic.types import FilePath

from .....jobs.base_cronicle_plugin import ReportedProgress
from .....lib.util import timed_run
from .....services.movie_file_processor.core import MovieFileProcessor
from .....settings import Settings


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
        yield {'progress': round(step_progress_result.total_percent, 2), 'perf': elapsed_times}


class DirectoryInput(BaseModel):
    api_key: str
    folder_path: DirectoryPath
    edl_ext: str


def process_directory(input: DirectoryInput, config: Settings) -> Iterator[ReportedProgress]:
    edls: list[FilePath] = []

    for edl in input.folder_path.glob(f'*{input.edl_ext}'):
        new_edl_name = edl.with_suffix(f'.pending_yml_{int(datetime.utcnow().timestamp())}')
        edl.rename(new_edl_name)
        edls.append(new_edl_name)

    def submit_job(edl_path: FilePath):
        params = {'file_path': str(edl_path.with_suffix('')), 'edl_ext': edl_path.suffix}
        res = requests.post(
            'http://localhost:3012/api/app/run_event/v1',
            headers={'X-API-Key': input.api_key},
            json={'title': 'Process Movie', 'params': params}
        )

        try:
            res.raise_for_status()
            json: dict[str, Any] = res.json()

            if json['code'] == 0:
                return '⏳ ENQUEUED' if json.get('queue') is not None else f'🔄️ PROCESSING (http://localhost:3012/#JobDetails?id={json['ids'][0]})'
            else:
                return f'⛔ ERROR "{json['code']}": {json['description']}'

        except requests.HTTPError as e:
            return e.args[0]

    def process_all():
        return {
            "table": {
                "title": "Movies to process",
                "header": ["Edl Path", "Job status"],
                "rows": [[str(edl_path.with_suffix('').name), submit_job(edl_path)] for edl_path in edls],
                "caption": f"{len(edls)} tasks."
            }
        }

    raw_table, process_time = timed_run(process_all)

    print(json.dumps(raw_table))
    yield {'progress': 1., 'perf': {'SubmitJobs': process_time}}
