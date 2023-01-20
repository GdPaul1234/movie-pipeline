import logging
from multiprocessing import Process, log_to_stderr
from pathlib import Path

from gui.segment_validators.main import main as run_gui


logger = logging.getLogger(__name__)

def command(options, config):
    logger.debug('args: %s', vars(options))
    dir_path = Path(options.dir)

    try:
        log_to_stderr(logging.DEBUG)

        for segment_file in dir_path.glob('*.segments.json'):
            movie_file = segment_file.with_name(segment_file.name.replace('.segments.json', ''))

            task = Process(target=run_gui, args=(movie_file, config))
            task.start()
            task.join()

    except Exception as e:
        logger.exception(e)

