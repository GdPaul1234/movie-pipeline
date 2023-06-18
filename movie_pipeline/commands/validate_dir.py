import logging
from pathlib import Path

from gui.segment_validators.main import main as run_gui
from settings import Settings

logger = logging.getLogger(__name__)

def command(options, config: Settings):
    logger.debug('args: %s', vars(options))
    filepath = Path(options.dir)

    try:
        if filepath.is_file():
            run_gui(filepath, config)
        elif filepath.is_dir():
            medias_path = [
                segment_file.with_name(segment_file.name.replace('.segments.json', ''))
                for segment_file in filepath.glob('*.segments.json')
            ]
            run_gui(medias_path, config)
        else:
            raise ValueError('Unknown file type')

    except Exception as e:
        logger.exception(e)

