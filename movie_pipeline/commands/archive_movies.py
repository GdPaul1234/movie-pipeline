import logging
from movie_pipeline.services.movie_archiver import MoviesArchiver

from settings import Settings

logger = logging.getLogger(__name__)

def command(options, config: Settings):
    logger.debug('args: %s', vars(options))
    MoviesArchiver(config).archive()
