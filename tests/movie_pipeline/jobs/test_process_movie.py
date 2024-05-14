import json
import re
import shutil
import sys
import textwrap
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import movie_pipeline.jobs.main as job

from ..concerns import copy_files, create_output_movies_directories, get_output_movies_directories, lazy_load_config_file

input_dir_path = Path(__file__).parent.joinpath('in')
video_path = input_dir_path.joinpath('channel 1_Movie Name_2022-11-1601-20.mp4')

output_dir_path, output_dir_movie_path, output_dir_serie_path, backup_dir_path = \
    get_output_movies_directories(Path(__file__).parent)


config_path = Path(__file__).parent / 'test_config.env'

class ProcessMovieTest(unittest.TestCase):
    def setUp(self) -> None:
        sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')
        copy_files([{'source': sample_video_path, 'destination': video_path},])

        create_output_movies_directories(Path(__file__).parent)

        # see https://github.com/jhuckaby/Cronicle/blob/master/docs/Plugins.md#json-input
        self.cronicle_json_input = {
            "id": "jihuxvagi01",
            "hostname": "joeretina.local",
            "command": "/usr/local/bin/my-plugin.js",
            "event": "3c182051",
            "now": 1449431125,
            "log_file": "/opt/cronicle/logs/jobs/jihuxvagi01.log",
            "params": {
                "myparam1": "90",
                "myparam2": "Value"
            }
        }

    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_of_process_movie(self, mock_stdout):
        edl_path = video_path.with_suffix('.mp4.yml')
        edl_path.write_text(textwrap.dedent('''\
            filename: Movie Name.mp4
            segments: 00:00:03.370-00:00:05.960,00:00:10.520-00:00:18.200,00:00:20.320-00:00:25.080,
        '''), encoding='utf-8')

        self.cronicle_json_input["params"] = {'file_path': str(video_path.absolute()), 'edl_ext': '.yml'}

        with patch.object(sys, 'argv', ["movie_pipeline_job_process_movie", json.dumps(self.cronicle_json_input)]):
            job.process_movie(config_path)

        output = mock_stdout.getvalue()
        self.assertRegex(output, re.compile(r'{"progress": [\d.]+'))
        self.assertRegex(output, re.compile(r'"perf": {"ProcessStep": [\d.]+, "BackupStep": [\d.]+}'))
        self.assertRegex(output, '{"complete": 1, "code": 0}')

    def tearDown(self) -> None:
        shutil.rmtree(input_dir_path)
        shutil.rmtree(output_dir_path)
