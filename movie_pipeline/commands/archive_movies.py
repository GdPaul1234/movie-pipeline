import logging

from ..lib.util import debug
from ..services.movie_archiver import MoviesArchiver
from ..settings import Settings

logger = logging.getLogger(__name__)

@debug(logger)
def command(config: Settings):
    MoviesArchiver(config).archive()
