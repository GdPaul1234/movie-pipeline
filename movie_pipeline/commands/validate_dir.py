import logging
from pathlib import Path

from gui.segment_validators.main import main as run_gui


logger = logging.getLogger(__name__)

def command(options, config):
    logger.debug('args: %s', vars(options))
    dir_path = Path(options.dir)

    try:
        for segment_file in dir_path.glob('*.segments.json'):
            movie_file = segment_file.with_name(segment_file.name.replace('.segments.json', ''))
            run_gui(movie_file, config)

    except Exception as e:
        logger.exception(e)

