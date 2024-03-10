import logging
from collections import deque
from pathlib import Path

from rich.progress import Progress

from ..lib.ui_factory import ProgressUIFactory
from ..lib.util import debug
from ..services.movie_file_processor.core import MovieFileProcessor
from ..services.movie_file_processor.folder_runner import MovieFileProcessorFolderRunner
from ..services.movie_file_processor.mpire_runner import MovieFileProcessorMpireRunner
from ..settings import Settings

logger = logging.getLogger(__name__)

@debug(logger)
def command(filepath: Path, edl_ext: str, config: Settings, use_web_runner=False):
    try:
        if filepath.is_file() and filepath.suffix == edl_ext:
            with Progress() as progress:
                deque(MovieFileProcessor(filepath, config).process_with_progress_tui(progress))
        elif filepath.is_dir():
            if use_web_runner:
                MovieFileProcessorMpireRunner(filepath, edl_ext, config).process_directory()
            else:
                progress_listener = ProgressUIFactory.create_process_listener()
                MovieFileProcessorFolderRunner(filepath, edl_ext, progress_listener, config).process_directory()
        else:
            raise ValueError('Unknown file type')
    except Exception as e:
        logger.exception(e)
