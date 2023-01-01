from dataclasses import dataclass
from typing import Any
import logging
import shutil
from pathlib import Path

from models.movie_file import LegacyMovieFile

logger = logging.getLogger(__name__)


@dataclass
class OriginalMovie:
    file_path: Path
    movie: LegacyMovieFile


@dataclass
class EdlFile:
    path: Path
    content: Any


class BackupPolicyExecutor:
    def __init__(self, edl_file: EdlFile, config) -> None:
        self._edl_file = edl_file
        self._config = config

    def _backup_original_movie(self, original_movie: OriginalMovie, backup_folder_path: Path):
        """Move original movie file to archive

        Args:
            original_movie (OriginalMovie): original movie to backup
            backup_folder_path (Path): path to store the original movie
        """
        dest_path = backup_folder_path.joinpath(original_movie.movie.title)
        dest_path.mkdir()

        logger.info('Move "%s" to "%s"', original_movie.file_path, dest_path)
        for file in original_movie.file_path.parent.glob(f'{original_movie.file_path.name}*'):
            shutil.move(file, dest_path)

    def _delete_original_serie(self, original_movie: OriginalMovie):
        """Delete original serie due to Backup Policy

        Args:
            original_movie (OriginalMovie): original serie to delete
        """
        logger.info('%s is serie, deleting it', original_movie.file_path)
        for file in original_movie.file_path.parent.glob(f'{original_movie.file_path.name}*'):
            file.unlink()

    def _skip_archive(self):
        """ Inactivate processing decision file
        """
        logger.info(
                'No backup folder found in config or backup is disabled for this file'
                ', inactivate processing decision file')
        self._edl_file.path.rename(self._edl_file.path.with_suffix('.yml.done'))

    def execute(self, original_file_path: Path):
        backup_folder = self._config.get('Paths', 'backup_folder', fallback=None)
        skip_backup = self._edl_file.content.get('skip_backup', False)

        if skip_backup or backup_folder is None:
            self._skip_archive()
        else:
            backup_folder_path = Path(backup_folder)
            original_movie = OriginalMovie(
                file_path=original_file_path,
                movie=LegacyMovieFile(self._edl_file.content['filename'])
            )

            if original_movie.movie.is_serie:
                self._delete_original_serie(original_movie)
            else:
                self._backup_original_movie(original_movie, backup_folder_path)
