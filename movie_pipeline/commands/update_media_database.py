import logging

from movie_pipeline.services.media_scanner import MediaScanner

from settings import Settings

logger = logging.getLogger(__name__)

def command(options, config: Settings):
    logger.debug('args: %s', vars(options))

    if config.MediaDatabase is None:
        raise ValueError('Missing MediaDatabase configuration in config')

    db_path = config.MediaDatabase.db_path

    try:
        with MediaScanner(db_path, config) as scanner:
            scanner.scan(options.files)
    except Exception as e:
        logger.exception(e)
