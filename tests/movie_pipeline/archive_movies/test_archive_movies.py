import os
import shutil
import unittest
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from movie_pipeline.commands.archive_movies import MoviesArchiver

from ..concerns import (copy_files, create_output_movies_directories,
                        get_output_movies_directories, lazy_load_config_file,
                        make_dirs)

output_dir_path, movie_dir_path, serie_dir_path, backup_dir_path = \
    get_output_movies_directories(Path(__file__).parent)

video_to_backup_path = movie_dir_path.joinpath('Old Movie Name', 'Old Movie Name.mp4')
video_not_to_backup_path = movie_dir_path.joinpath('Movie Name', 'Movie Name.mp4')

archive_movie_dir_path = backup_dir_path.joinpath('Films')

lazy_config = lazy_load_config_file(Path(__file__).parent)


class ArchiveMoviesTest(unittest.TestCase):
    def setUp(self) -> None:
        create_output_movies_directories(Path(__file__).parent)

        pvr_movie_backup_dir_path = backup_dir_path.joinpath('PVR', 'Films')
        video_not_to_backup_archive_path = pvr_movie_backup_dir_path.joinpath('Movie Name', 'Movie Name.mp4')
        video_to_backup_archive_path = pvr_movie_backup_dir_path.joinpath('Old Movie Name', 'Old Movie Name.mp4')

        sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')

        def change_created_at_to_past(path: Path):
            past_datetime = datetime.now().timestamp() - timedelta(days=5).total_seconds()
            os.utime(path, (past_datetime, past_datetime))

        copy_files([
            {'source': sample_video_path, 'destination': video_not_to_backup_path},
            {'source': video_not_to_backup_path, 'destination': video_not_to_backup_archive_path},
            # ---
            {'source': sample_video_path, 'destination': video_to_backup_path, 'after_copy': change_created_at_to_past},
            {'source': video_to_backup_path, 'destination': video_to_backup_archive_path}
        ])

        archive_movie_dir_path.mkdir()

    def test_is_old_movie(self):
        movie_archiver = MoviesArchiver(lazy_config())

        self.assertTrue(movie_archiver._is_old_movie(video_to_backup_path))
        self.assertFalse(movie_archiver._is_old_movie(video_not_to_backup_path))

    def test_archive_abort(self):
        movie_archiver = MoviesArchiver(lazy_config())

        with patch('sys.stdin', StringIO('n\n')):
            movie_archiver.archive()

        self.assertEqual([], list(archive_movie_dir_path.iterdir()))

    def test_archive_confirm(self):
        movie_archiver = MoviesArchiver(lazy_config())

        with patch('sys.stdin', StringIO('Y')):
            movie_archiver.archive()

        self.assertTrue(archive_movie_dir_path.joinpath('Old Movie Name', 'Old Movie Name.mp4').exists())
        self.assertFalse(archive_movie_dir_path.joinpath('Movie Name', 'Movie Name.mp4').exists())

    def tearDown(self) -> None:
        shutil.rmtree(output_dir_path)
