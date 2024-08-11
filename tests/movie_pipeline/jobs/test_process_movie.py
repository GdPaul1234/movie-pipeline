import json
import re
import shutil
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import movie_pipeline.jobs.main as job

from ..concerns import (
    copy_files, create_output_movies_directories, get_base_cronicle_json_input, get_output_movies_directories,
    get_movie_edl_file_content
)


class ProcessMovieTest(unittest.TestCase):
    def setUp(self) -> None:
        self.input_dir_path = Path(__file__).parent / 'in'
        self.video_path = self.input_dir_path / 'channel 1_Movie Name_2022-11-1601-20.mp4'
        self.output_dir_path, *_, backup_dir_path = get_output_movies_directories(Path(__file__).parent)
        self.config_path = Path(__file__).parent / 'test_config.env'

        sample_video_path = Path(__file__).parent.parent / 'ressources' / 'counter-30s.mp4'
        copy_files([{'source': sample_video_path, 'destination': self.video_path}])

        create_output_movies_directories(Path(__file__).parent)

        archive_movie_dir_path = backup_dir_path / 'Films'
        archive_movie_dir_path.mkdir()

        self.cronicle_json_input = get_base_cronicle_json_input()

    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_of_process_movie(self, mock_stdout):
        edl_path = self.video_path.with_suffix('.mp4.yml')
        edl_path.write_text(get_movie_edl_file_content(), encoding='utf-8')

        self.cronicle_json_input["params"] = {'file_path': str(self.video_path.absolute()), 'edl_ext': '.yml'}

        with patch.object(sys, 'argv', ["movie_pipeline_job_process_movie", json.dumps(self.cronicle_json_input)]):
            job.process_movie(self.config_path)

        output = mock_stdout.getvalue()
        self.assertRegex(output, re.compile(r'{"progress": [\d.]+'))
        self.assertRegex(output, re.compile(r'"perf": {"ProcessStep": [\d.]+, "BackupStep": [\d.]+}'))
        self.assertRegex(output, '{"complete": 1, "code": 0}')

    def tearDown(self) -> None:
        shutil.rmtree(self.input_dir_path)
        shutil.rmtree(self.output_dir_path)
