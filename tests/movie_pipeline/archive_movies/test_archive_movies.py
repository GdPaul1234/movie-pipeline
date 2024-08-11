from collections import deque
import os
import shutil
import unittest
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from movie_pipeline.services.movie_archiver.movie_archiver import MoviesArchiver

from ..concerns import copy_files, create_output_movies_directories, get_output_movies_directories, lazy_load_config_file


class ArchiveMoviesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir_path, movie_dir_path, self.serie_dir_path, backup_dir_path = get_output_movies_directories(Path(__file__).parent)
        self.video_to_backup_path = movie_dir_path.joinpath('Old Movie Name', 'Old Movie Name.mp4')
        self.video_not_to_backup_path = movie_dir_path.joinpath('Movie Name', 'Movie Name.mp4')
        self.lazy_config = lazy_load_config_file(Path(__file__).parent)

        create_output_movies_directories(Path(__file__).parent)

        pvr_movie_backup_dir_path = backup_dir_path.joinpath('PVR', 'Films')
        video_not_to_backup_archive_path = pvr_movie_backup_dir_path.joinpath('Movie Name', 'Movie Name.mp4')
        video_to_backup_archive_path = pvr_movie_backup_dir_path.joinpath('Old Movie Name', 'Old Movie Name.mp4')

        sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')

        def change_created_at_to_past(path: Path):
            past_datetime = datetime.now().timestamp() - timedelta(days=5).total_seconds()
            os.utime(path, (past_datetime, past_datetime))

        copy_files([
            {'source': sample_video_path, 'destination': self.video_not_to_backup_path},
            {'source': self.video_not_to_backup_path, 'destination': video_not_to_backup_archive_path},
            # ---
            {'source': sample_video_path, 'destination': self.video_to_backup_path, 'after_copy': change_created_at_to_past},
            {'source': self.video_to_backup_path, 'destination': video_to_backup_archive_path}
        ])

        self.archive_movie_dir_path = backup_dir_path.joinpath('Films')
        self.archive_movie_dir_path.mkdir()
        
        self.movie_archiver = MoviesArchiver(self.lazy_config())

    def test_is_old_movie(self):
        self.assertTrue(self.movie_archiver._is_old_movie(self.video_to_backup_path))
        self.assertFalse(self.movie_archiver._is_old_movie(self.video_not_to_backup_path))

    def test_archive_abort(self):
        with patch('sys.stdin', StringIO('n\n')):
            deque(self.movie_archiver.archive_with_progress())

        self.assertEqual([], list(self.archive_movie_dir_path.iterdir()))

    def test_archive_confirm(self):
        with patch('sys.stdin', StringIO('Y')):
            deque(self.movie_archiver.archive_with_progress())

        self.assertTrue(self.archive_movie_dir_path.joinpath('Old Movie Name', 'Old Movie Name.mp4').exists())
        self.assertFalse(self.archive_movie_dir_path.joinpath('Movie Name', 'Movie Name.mp4').exists())

    def tearDown(self) -> None:
        shutil.rmtree(self.output_dir_path)
