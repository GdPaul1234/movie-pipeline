from collections import deque
import json
import os
import re
import shutil
import sys
import unittest
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import movie_pipeline.jobs.main as job

from ..concerns import copy_files, create_output_movies_directories, get_base_cronicle_json_input, get_output_movies_directories


class ArchiveMoviesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir_path, movie_dir_path, _, backup_dir_path = get_output_movies_directories(Path(__file__).parent)
        video_to_backup_path = movie_dir_path.joinpath('Old Movie Name', 'Old Movie Name.mp4')
        video_not_to_backup_path = movie_dir_path.joinpath('Movie Name', 'Movie Name.mp4')
        self.config_path = Path(__file__).parent / 'test_config.env'

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

        self.archive_movie_dir_path = backup_dir_path.joinpath('Films')
        self.archive_movie_dir_path.mkdir()
        
        self.cronicle_json_input = get_base_cronicle_json_input()

    @patch('sys.stdout', new_callable=StringIO)
    def test_dry_archive_movies(self, mock_stdout):
        self.cronicle_json_input["params"] = {"dry": True}

        with patch.object(sys, 'argv', ["movie_pipeline_job_archive_movies", json.dumps(self.cronicle_json_input)]):
            job.archive_movies(self.config_path)

        output = mock_stdout.getvalue()
        self.assertRegex(output, '{"table": {"title": "Movies to archive", "header":')
        self.assertRegex(output, re.compile(r'{"progress": [\d.]+'))
        self.assertRegex(output, '{"complete": 1, "code": 0}')

        self.assertEqual([], list(self.archive_movie_dir_path.iterdir()))

    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_of_archive_movies(self, mock_stdout):
        self.cronicle_json_input["params"] = {}

        with patch.object(sys, 'argv', ["movie_pipeline_job_archive_movies", json.dumps(self.cronicle_json_input)]):
            job.archive_movies(self.config_path)

        output = mock_stdout.getvalue()
        self.assertRegex(output, re.compile(r'{"progress": [\d.]+'))
        self.assertRegex(output, re.compile(r'"perf": {"ArchiveMovies": [\d.]+}'))
        self.assertRegex(output, '{"complete": 1, "code": 0}')

        self.assertTrue(self.archive_movie_dir_path.joinpath('Old Movie Name', 'Old Movie Name.mp4').exists())
        self.assertFalse(self.archive_movie_dir_path.joinpath('Movie Name', 'Movie Name.mp4').exists())

    def tearDown(self) -> None:
        shutil.rmtree(self.output_dir_path)
