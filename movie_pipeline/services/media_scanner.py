import logging
from pathlib import Path

from rich.progress import Progress

from settings import Settings

from .media_database_updater import MediaDatabaseUpdater

logger = logging.getLogger(__name__)


class MediaScanner:
    def __init__(self, db_path: Path, config: Settings) -> None:
        self._media_db_updater = MediaDatabaseUpdater(db_path)
        self._config = config

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._media_db_updater.close()
        return False

    def _scan_file (self, filepath: Path):
        self._media_db_updater.insert_media(nfo_path=filepath)

    def _scan_dir (self, dir_path: Path):
        nfos = set(dir_path.glob('**/*.nfo'))
        nfo_to_scan = nfos - self._media_db_updater.already_inserted_nfos
        logger.info(f'Found {len(nfos)} NFOs, {len(nfo_to_scan)} to scan')

        nfo_errors = []

        with Progress() as progress:
            for nfo_path in progress.track(nfo_to_scan):
                try:
                    message = f'Inserting "{str(nfo_path)}"...'
                    logger.info(message); progress.console.log(message)
                    self._media_db_updater.insert_media(nfo_path)
                except Exception as e:
                    logger.exception(e)
                    nfo_errors.append(nfo_path)

        if len(nfo_errors) > 0:
            logger.warning(f"Errors found in:\n{list(map(str, nfo_errors))}")

    def scan(self, paths: list[Path]):
        if self._config.MediaDatabase.clean_after_update: # type: ignore
            logger.info('Cleaning database...')
            self._media_db_updater.clean_media_database()

        for path in paths:
            logger.info(f'Scanning "{str(path)}"...')

            if path.is_file() and path.suffix == '.nfo':
                self._scan_file(path)
            elif path.is_dir():
                self._scan_dir(path)
            else:
                logger.error('Unknown file type for %s', str(path))
