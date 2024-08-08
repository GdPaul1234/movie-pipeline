import logging
import time
from typing import Iterator

from pydantic import BaseModel

from ....jobs.base_cronicle_plugin import ReportedProgress
from ....services.movie_archiver.movie_archiver import MoviesArchiver
from ....settings import Settings

logger = logging.getLogger(__name__)


class Input(BaseModel):
    dry: bool = False


def archive_movies(input: Input, config: Settings) -> Iterator[ReportedProgress]:
    start_time = time.perf_counter()
    
    for progress_percent in MoviesArchiver(config).archive_with_progress(dry=input.dry, interactive=False):
        end_time = time.perf_counter()
        elapsed_times: dict[str, float] = {"ArchiveMovies": end_time - start_time}
        yield {'progress': round(progress_percent, 2), 'perf': elapsed_times}
