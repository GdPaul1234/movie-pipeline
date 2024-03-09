import logging

from settings import Settings
from util import debug

from ..services.movie_archiver import MoviesArchiver

logger = logging.getLogger(__name__)

@debug(logger)
def command(config: Settings):
    MoviesArchiver(config).archive()
