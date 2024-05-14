from datetime import datetime
from typing import Iterator

from pydantic import BaseModel
from pydantic.types import FilePath

from .....jobs.base_cronicle_plugin import ReportedProgress
from .....services.movie_file_processor.core import MovieFileProcessor
from .....settings import Settings

class Input(BaseModel):
    file_path: FilePath
    edl_ext: str


def process_file(input: Input, config: Settings) -> Iterator[ReportedProgress]:
    edl = input.file_path.with_suffix(f'{input.file_path.suffix}{input.edl_ext}')
    new_edl_name = edl.with_suffix(f'.pending_yml_{int(datetime.utcnow().timestamp())}')
    edl.rename(new_edl_name)

    movie_file_processor = MovieFileProcessor(new_edl_name, config)
    elapsed_times: dict[str, float] = {}

    for step_progress_result in movie_file_processor.movie_file_processor_root_step.process_all():
        elapsed_times[type(step_progress_result.current_step).__name__] = round(step_progress_result.current_step_elapsed_time, 2)
        yield {'progress': round(step_progress_result.total_percent, 2), 'perf': elapsed_times}
