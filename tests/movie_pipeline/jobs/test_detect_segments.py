import json
import re
import shutil
import sys
import textwrap
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import ffmpeg

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

        sample_logo_picture_path = Path(__file__).parent.parent / 'ressources' / 'features' / 'segments_detector' / 'logo' / 'channel 1.bmp'
        self.sample_logo_picture_path = self.input_dir_path / 'logo' / 'channel 1.bmp'

        sample_logo_config_path = Path(__file__).parent.parent / 'ressources' / 'features' / 'segments_detector' / 'logo' / 'channel 1.ini'
        self.sample_logo_config_path = self.input_dir_path / 'logo' / 'channel 1.ini'

        copy_files([
            {'source': sample_video_path, 'destination': self.video_path},
            {'source': sample_video_path, 'destination': self.other_video_path},
            {'source': sample_logo_picture_path, 'destination': self.sample_logo_picture_path},
            {'source': sample_logo_config_path, 'destination': self.sample_logo_config_path}
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

        self.expected_video_segments_content = {
            'match_template': [
                '00:00:00.200-00:00:03.400,00:00:08.800-00:00:14.200,00:00:19.200-00:00:24.200',
                '00:00:00.240-00:00:03.400,00:00:08.760-00:00:14.200,00:00:19.200-00:00:24.200'
            ],
            'crop': [
                '00:00:00.400-00:00:03.200,00:00:08.800-00:00:14.000,00:00:19.000-00:00:24.200',
                '00:00:00.486-00:00:03.162,00:00:08.512-00:00:14.000,00:00:19.000-00:00:24.200'
            ],
            'axcorrelate_silence': [
                '00:00:00.000-00:00:03.475,00:00:08.153-00:00:14.395,00:00:19.288-00:00:24.320',
                '00:00:00.000-00:00:07.788,00:00:08.153-00:00:14.464,00:00:19.289-00:00:24.320'
            ]
        }

    def test_log_progress_of_detected_segments(self):
        for detector_key, expected_video_segments_any_content in self.expected_video_segments_content.items():
            with self.subTest(detector_key=detector_key):
                self.cronicle_json_input["params"] = {'file_path': str(self.video_path.absolute()), 'detector': detector_key}

                with patch.object(sys, 'stdin', StringIO(json.dumps(self.cronicle_json_input))):
                    with patch.object(sys, 'stdout', new_callable=StringIO) as mock_stdout:
                        job.detect_segments(self.config_path)

                self.assertProgress(output=mock_stdout.getvalue())
            
                video_segments_content = self.assertAndReadOnlyVideoSegmentPathExists()
                self.assertIn(video_segments_content[detector_key], expected_video_segments_any_content)

    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_of_detected_segments_with_auto_detect_select_match_template(self, mock_stdout):
        self.cronicle_json_input["params"] = {'file_path': str(self.video_path.absolute()), 'detector': 'auto'}

        with patch.object(sys, 'stdin', StringIO(json.dumps(self.cronicle_json_input))):
            job.detect_segments(self.config_path)

        self.assertProgress(output=mock_stdout.getvalue())

        video_segments_content = self.assertAndReadOnlyVideoSegmentPathExists()
        self.assertIn(video_segments_content['auto'], self.expected_video_segments_content['match_template'])

    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_of_detected_segments_with_auto_detect_select_crop_detect(self, mock_stdout):
        self.cronicle_json_input["params"] = {'file_path': str(self.video_path.absolute()), 'detector': 'auto'}

        # remove logo to force crop detect instead of eligible match_template detect
        self.sample_logo_picture_path.unlink()
        self.sample_logo_config_path.unlink()

        with patch.object(sys, 'stdin', StringIO(json.dumps(self.cronicle_json_input))):
            job.detect_segments(self.config_path)

        self.assertProgress(output=mock_stdout.getvalue())

        video_segments_content = self.assertAndReadOnlyVideoSegmentPathExists()
        self.assertIn(video_segments_content['auto'], self.expected_video_segments_content['crop'])

    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_of_detected_segments_with_auto_detect_select_axcorrelate_silence_detect(self, mock_stdout):
        self.cronicle_json_input["params"] = {'file_path': str(self.video_path.absolute()), 'detector': 'auto'}

        # remove logo to force crop detect instead of eligible match_template detect
        self.sample_logo_picture_path.unlink()
        self.sample_logo_config_path.unlink()

        # crop video to discard crop detect by removing the 'cinema' aspect ratio
        nb_audio_streams = len(ffmpeg.probe(self.video_path, select_streams='a')['streams'])
        cropped_video_path = self.video_path.with_stem(f'{self.video_path.stem}_cropped')

        v1 = ffmpeg.input(str(self.video_path)).video.filter_('scale', w='1.31*iw', h='1.31*ih').filter_('crop', w='iw/1.31', h='ih/1.31')
        a1 = ffmpeg.input(str(self.video_path)).audio

        ffmpeg.output(
            v1, a1,
            str(cropped_video_path),
            **{f'map_metadata:s:a:{index}': f'0:s:a:{index}' for index in range(nb_audio_streams)}
        ).run()

        self.video_path.unlink()
        cropped_video_path.rename(self.video_path)

        with patch.object(sys, 'stdin', StringIO(json.dumps(self.cronicle_json_input))):
            job.detect_segments(self.config_path)

        self.assertProgress(output=mock_stdout.getvalue())

        video_segments_content = self.assertAndReadOnlyVideoSegmentPathExists()
        self.assertIn(video_segments_content['auto'], self.expected_video_segments_content['axcorrelate_silence'])

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
