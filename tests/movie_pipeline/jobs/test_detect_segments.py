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

from ..concerns import copy_files, create_output_movies_directories, get_base_cronicle_json_input, get_output_movies_directories


class DetectSegmentsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.input_dir_path = Path(__file__).parent / 'in'
        self.video_path = self.input_dir_path / 'channel 1_Movie Name_2022-11-1601-20.mp4'
        self.other_video_path = self.input_dir_path / 'channel 1_Other Movie Name_2022-11-1601-20.mp4'
        self.output_dir_path, *_, backup_dir_path = get_output_movies_directories(Path(__file__).parent)
        self.config_path = Path(__file__).parent / 'test_config.env'

        sample_video_path = Path(__file__).parent.parent / 'ressources' / 'features' / 'segments_detector' / 'segments_detector test video.mp4'
        copy_files([
            {'source': sample_video_path, 'destination': self.video_path},
            {'source': sample_video_path, 'destination': self.other_video_path}
        ])

        video_metadata_path = self.video_path.with_suffix(f'{self.video_path.suffix}.metadata.json')
        video_metadata_path.write_text(textwrap.dedent('''\
        {
            "fullpath": "/volume1/video/PVR/channel 1_Movie Name_2022-11-1601-20.ts",
            "basename": "channel 1_Movie Name_2022-11-1601-20.ts",
            "channel": "channel 1",
            "title": "Movie Name",
            "sub_title": "",
            "description": "",
            "start_real": 1715512977,
            "stop_real": 1715517943,
            "error_message": "OK",
            "nb_data_errors": 6,
            "recording_id": "1ece3e4c96d05e090a48b921bf6d6588"
        }
        '''), encoding='utf-8')

        create_output_movies_directories(Path(__file__).parent)

        archive_movie_dir_path = backup_dir_path / 'Films'
        archive_movie_dir_path.mkdir()

        self.cronicle_json_input = get_base_cronicle_json_input()

    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_of_detected_segments_with_match_template(self, mock_stdout):
        self.cronicle_json_input["params"] = {'file_path': str(self.video_path.absolute()), 'detector': 'match_template'}

        with patch.object(sys, 'stdin', StringIO(json.dumps(self.cronicle_json_input))):
            job.detect_segments(self.config_path)

        self.assertProgress(output=mock_stdout.getvalue())
     
        video_segments_content = self.assertAndReadOnlyVideoSegmentPathExists()
        self.assertEqual('00:00:00.200-00:00:03.400,00:00:08.800-00:00:14.200,00:00:19.200-00:00:24.200', video_segments_content['match_template'])

    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_of_detected_segments_with_crop_detect(self, mock_stdout):
        self.cronicle_json_input["params"] = {'file_path': str(self.video_path.absolute()), 'detector': 'crop'}

        with patch.object(sys, 'stdin', StringIO(json.dumps(self.cronicle_json_input))):
            job.detect_segments(self.config_path)

        self.assertProgress(output=mock_stdout.getvalue())

        video_segments_content = self.assertAndReadOnlyVideoSegmentPathExists()
        self.assertEqual('00:00:00.080-00:00:03.280,00:00:08.600-00:00:14.320,00:00:18.920-00:00:24.160', video_segments_content['crop'])

    def assertProgress(self, output: str):
        self.assertRegex(output, re.compile(r'{"progress": [\d.]+'))
        self.assertRegex(output, re.compile(r'"perf": {"Item0": [\d.]+}'))
        self.assertRegex(output, '{"complete": 1, "code": 0}')

    def assertAndReadOnlyVideoSegmentPathExists(self):
        video_segments_path = self.video_path.with_suffix(f'{self.video_path.suffix}.segments.json')
        other_video_segments_path = self.other_video_path.with_suffix(f'{self.other_video_path.suffix}.segments.json')
        self.assertTrue(video_segments_path.exists())
        self.assertFalse(other_video_segments_path.exists())
        return json.loads(video_segments_path.read_text())

    def tearDown(self) -> None:
        shutil.rmtree(self.input_dir_path)
        shutil.rmtree(self.output_dir_path)
