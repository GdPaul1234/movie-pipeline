import logging

from settings import Settings

from ..services.movie_archiver import MoviesArchiver

logger = logging.getLogger(__name__)

def command(options, config: Settings):
    logger.debug('args: %s', vars(options))
    MoviesArchiver(config).archive()
