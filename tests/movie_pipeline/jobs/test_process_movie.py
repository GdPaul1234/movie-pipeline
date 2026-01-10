import json
import re
import shutil
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import movie_pipeline.jobs.main as job

from ..concerns import copy_files, create_output_movies_directories, get_base_xyops_json_input, get_movie_edl_file_content, get_output_movies_directories, get_serie_edl_file_content


class ProcessMovieTest(unittest.TestCase):
    def setUp(self) -> None:
        self.input_dir_path = Path(__file__).parent / 'in'
        self.video_path = self.input_dir_path / 'channel 1_Movie Name_2022-11-1601-20.mp4'
        self.serie_path = self.input_dir_path / 'channel 1_Serie Name S01E23_2022-11-1601-20.mp4'

        self.output_dir_path, *_, backup_dir_path = get_output_movies_directories(Path(__file__).parent)
        self.config_path = Path(__file__).parent / 'test_config.env'

        sample_video_path = Path(__file__).parent.parent / 'ressources' / 'counter-30s.mp4'
        copy_files([
            {'source': sample_video_path, 'destination': self.video_path},
            {'source': sample_video_path, 'destination': self.serie_path}
        ])

        create_output_movies_directories(Path(__file__).parent)

        archive_movie_dir_path = backup_dir_path / 'Films'
        archive_movie_dir_path.mkdir()

        logo_dir_path = self.input_dir_path / 'logo'
        logo_dir_path.mkdir(parents=True)

        self.xyops_json_input = get_base_xyops_json_input()

    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_of_process_movie(self, mock_stdout):
        edl_path = self.video_path.with_suffix('.mp4.yml')
        edl_path.write_text(get_movie_edl_file_content(), encoding='utf-8')

        self.xyops_json_input["params"] = {'file_path': str(self.video_path.absolute()), 'edl_ext': '.yml'}

        with patch.object(sys, 'stdin', StringIO(json.dumps(self.xyops_json_input))):
            job.process_movie(self.config_path)

        output = mock_stdout.getvalue()
        self.assertRegex(output, re.compile(r'{"xy": 1, "progress": [\d.]+'))
        self.assertRegex(output, re.compile(r'"perf": {"ProcessStep": [\d.]+, "BackupStep": [\d.]+}'))
        self.assertRegex(output, '{"xy": 1, "code": 0}')

    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_of_process_directory(self, mock_stdout):
        edl_path = self.video_path.with_suffix('.mp4.yml')
        edl_path.write_text(get_movie_edl_file_content(), encoding='utf-8')

        edl_serie_path = self.serie_path.with_suffix('.mp4.yml')
        edl_serie_path.write_text(get_serie_edl_file_content(), encoding='utf-8')

        self.xyops_json_input["params"] = {'folder_path': str(self.input_dir_path.absolute()), 'edl_ext': '.yml'}

        with patch.object(sys, 'stdin', StringIO(json.dumps(self.xyops_json_input))):
            job.process_directory(self.config_path)

        output = mock_stdout.getvalue()

        expected_date_output = json.dumps({
            "xy": 1,
            "data": {
                "process_file_inputs": [
                    {'file_path': str(self.video_path.absolute()), 'edl_ext': '__edl_ext_regex__'},
                    {'file_path': str(self.serie_path.absolute()), 'edl_ext': '__edl_ext_regex__'}
                ]
            }
        })
        self.assertRegex(output, re.compile(re.escape(expected_date_output).replace('__edl_ext_regex__', r'\.pending_yml_\d+')))

        self.assertRegex(output, re.compile(r'{"xy": 1, "progress": [\d.]+'))
        self.assertRegex(output, re.compile(r'"perf": {"SubmitJobs": [\d.]+'))
        self.assertRegex(output, '{"xy": 1, "code": 0}')


    def tearDown(self) -> None:
        shutil.rmtree(self.input_dir_path)
        shutil.rmtree(self.output_dir_path)
