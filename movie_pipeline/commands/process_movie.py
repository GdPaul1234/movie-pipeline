import logging
from pathlib import Path

from rich.progress import Progress
from movie_pipeline.services.movie_file_processor import MovieFileProcessor
from movie_pipeline.services.movie_file_processor_folder_runner import MovieFileProcessorFolderRunner

from settings import Settings

from ..lib.ui_factory import (ProgressUIFactory)

logger = logging.getLogger(__name__)

def command(options, config: Settings):
    logger.debug('args: %s', vars(options))

    filepath = Path(options.file)
    edl_ext: str = options.custom_ext

    try:
        if filepath.is_file() and filepath.suffix == edl_ext:
            with Progress() as progress:
                MovieFileProcessor(filepath, progress, config).process()
        elif filepath.is_dir():
            progress_listener = ProgressUIFactory.create_process_listener()
            MovieFileProcessorFolderRunner(filepath, edl_ext, progress_listener, config).process_directory()
        else:
            raise ValueError('Unknown file type')
    except Exception as e:
        logger.exception(e)
