import logging
from pathlib import Path

from movie_pipeline.services.edl_scaffolder import PathScaffolder

from settings import Settings

logger = logging.getLogger(__name__)

def command(options, config: Settings):
    logger.debug('args: %s', vars(options))
    dir_path = Path(options.dir)

    try:
        PathScaffolder(dir_path, config).scaffold()
    except Exception as e:
        logger.exception(e)
