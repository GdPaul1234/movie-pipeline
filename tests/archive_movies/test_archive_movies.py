from argparse import Namespace
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
import os
import shutil
import unittest
from unittest.mock import patch

from commands.archive_movies import MoviesArchiver
from config_loader import ConfigLoader

output_dir_path = Path(__file__).parent.joinpath('out')
backup_dir_path = output_dir_path.joinpath('backup')

movie_dir_path = output_dir_path.joinpath('Films')
video_to_backup_path = movie_dir_path.joinpath('Old Movie Name', 'Old Movie Name.mp4')
video_not_to_backup_path = movie_dir_path.joinpath('Movie Name', 'Movie Name.mp4')

archive_movie_dir_path = backup_dir_path.joinpath('Films')

config_path = Path(__file__).parent.joinpath('test_config.ini')
options = Namespace()
setattr(options, 'config_path', config_path)
config = ConfigLoader(options).config

class ArchiveMoviesTest(unittest.TestCase):
    def setUp(self) -> None:
        movie_dir_path.mkdir(parents=True)
        sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')

        # movie 1, recent (not to backup)
        video_not_to_backup_path.parent.mkdir(parents=True)
        shutil.copyfile(sample_video_path, video_not_to_backup_path)

        # movie 2, to backup
        video_to_backup_path.parent.mkdir(parents=True)
        shutil.copyfile(sample_video_path, video_to_backup_path)
        past_datetime = datetime.now().timestamp() - timedelta(days=5).total_seconds()
        os.utime(video_to_backup_path, (past_datetime, past_datetime))

        # backups
        pvr_movie_backup_dir_path = backup_dir_path.joinpath('PVR', 'Films')
        pvr_movie_backup_dir_path.mkdir(parents=True)

        video_not_to_backup_archive_path = pvr_movie_backup_dir_path.joinpath('Movie Name')
        video_not_to_backup_archive_path.mkdir()
        shutil.copy2(video_not_to_backup_path, video_not_to_backup_archive_path)

        video_to_backup_archive_path = pvr_movie_backup_dir_path.joinpath('Old Movie Name')
        video_to_backup_archive_path.mkdir()
        shutil.copy2(video_to_backup_path, video_to_backup_archive_path)

        archive_movie_dir_path.mkdir()

    def test_is_old_movie(self):
        movie_archiver = MoviesArchiver(config)

        self.assertTrue(movie_archiver._is_old_movie(video_to_backup_path))
        self.assertFalse(movie_archiver._is_old_movie(video_not_to_backup_path))

    def test_archive_arbort(self):
        movie_archiver = MoviesArchiver(config)

        with patch('sys.stdin', StringIO('n\n')):
            movie_archiver.archive()

        self.assertEqual([], list(archive_movie_dir_path.iterdir()))

    def test_archive_confirm(self):
        movie_archiver = MoviesArchiver(config)

        with patch('sys.stdin', StringIO('Y')):
            movie_archiver.archive()

        self.assertTrue(archive_movie_dir_path.joinpath('Old Movie Name', 'Old Movie Name.mp4').exists())
        self.assertFalse(archive_movie_dir_path.joinpath('Movie Name', 'Movie Name.mp4').exists())

    def tearDown(self) -> None:
        shutil.rmtree(output_dir_path)
