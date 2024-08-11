import json
import logging
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Literal

from ...settings import Settings

logger = logging.getLogger(__name__)

class MoviesArchiver:
    def __init__(self, config: Settings) -> None:
        if config.Archive is None:
            raise ValueError('Missing Archive configuration in config')

        self._movies_path = config.Paths.movies_folder
        self._base_backup_path = config.Archive.base_backup_path
        self._movies_archive_folder = config.Archive.movies_archive_folder
        self._max_retention_in_s = config.Archive.max_retention_in_s

    def _is_old_movie(self, movie: Path) -> bool:
        today = time.time()
        last_modified_time = movie.stat().st_mtime
        return (today - last_modified_time) >= self._max_retention_in_s

    def _report_movies_to_archive(self, movies: list[Path], format: Literal['json', 'table'] = 'table') -> str:
        # cf https://github.com/jhuckaby/Cronicle/blob/master/docs/Plugins.md#custom-data-tables
        raw_table = {
            "table": {
                "title": "Movies to archive",
                "header": ["Modified at", "File Name"],
                "rows": [[
                    datetime.fromtimestamp(movie.stat().st_mtime).strftime('%Y-%m-%d-%H:%M'),
                    movie.name
                ] for movie in movies],
                "caption": f"{len(movies)} movies."
            }
        }

        if format == 'json':
            return json.dumps(raw_table)
        else:
            return '\n'.join(['\t'.join(row) for row in raw_table['table']['rows']])

    def _do_archive_with_progress(self, old_movies: list[Path]):
        old_movies_size = len(old_movies)

        for index, old_movie in enumerate(old_movies):
            parent_dir = old_movie.parent
            backup_parent_dir = self._base_backup_path / 'PVR' / 'Films' / parent_dir.name
            dest_path = self._movies_archive_folder /parent_dir.name

            try:
                logger.info('Archiving %s\n  to %s', backup_parent_dir, dest_path)
                backup_parent_dir.replace(dest_path)

                logger.info('Deleting %s', parent_dir)
                shutil.rmtree(parent_dir)
            except FileNotFoundError:
                logger.error('Skipping %s, backup not found', parent_dir.name)

            yield index / float(old_movies_size)            

    def archive_with_progress(self, dry=False, interactive=True):
        logger.info('options: %s', vars(self))

        movie_dirs = [x for x in self._movies_path.iterdir() if x.is_dir()]
        movies = [x for m_dir in movie_dirs for x in m_dir.iterdir() if x.is_file() and x.suffix == '.mp4']
        old_movies = sorted([movie for movie in movies if self._is_old_movie(movie)], key=lambda movie: movie.stat().st_mtime)

        if interactive:
            logger.info(f'\n{self._report_movies_to_archive(old_movies)}')
            choice = input(f'About to archive {len(old_movies)} movies. OK? (Y/n) ')
            dry = choice!= 'Y'
        else:
            print(self._report_movies_to_archive(old_movies, format='json'))

        if not dry:
            yield from self._do_archive_with_progress(old_movies)
        else:
            logger.info('Operation aborted')
            yield 1.
