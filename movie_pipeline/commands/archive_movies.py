from collections import deque
import logging

from ..lib.util import debug
from ..services.movie_archiver.movie_archiver import MoviesArchiver
from ..settings import Settings

logger = logging.getLogger(__name__)

@debug(logger)
def command(config: Settings):
    deque(MoviesArchiver(config).archive_with_progress())
