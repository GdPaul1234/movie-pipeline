import json
import re
import shutil
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import movie_pipeline.jobs.main as job

from ..concerns import copy_files, create_output_movies_directories, get_base_cronicle_json_input, get_movie_edl_file_content, get_output_movies_directories, get_serie_edl_file_content


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

        self.cronicle_json_input = get_base_cronicle_json_input()

    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_of_process_movie(self, mock_stdout):
        edl_path = self.video_path.with_suffix('.mp4.yml')
        edl_path.write_text(get_movie_edl_file_content(), encoding='utf-8')

        self.cronicle_json_input["params"] = {'file_path': str(self.video_path.absolute()), 'edl_ext': '.yml'}

        with patch.object(sys, 'stdin', StringIO(json.dumps(self.cronicle_json_input))):
            job.process_movie(self.config_path)

        output = mock_stdout.getvalue()
        self.assertRegex(output, re.compile(r'{"progress": [\d.]+'))
        self.assertRegex(output, re.compile(r'"perf": {"ProcessStep": [\d.]+, "BackupStep": [\d.]+}'))
        self.assertRegex(output, '{"complete": 1, "code": 0}')

    @patch('movie_pipeline.services.movie_file_processor.runner.cronicle.cronicle_runner.requests.post')
    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_of_process_directory(self, mock_stdout, mock_post):
        edl_path = self.video_path.with_suffix('.mp4.yml')
        edl_path.write_text(get_movie_edl_file_content(), encoding='utf-8')

        edl_serie_path = self.serie_path.with_suffix('.mp4.yml')
        edl_serie_path.write_text(get_serie_edl_file_content(), encoding='utf-8')

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.side_effect = [{'code': 0, 'ids': ['23f5c37f']}, {'code': 0, 'ids': [], 'queue': 1}]

        self.cronicle_json_input["params"] = {'api_key': 'CRONICLE_API_KEY', 'folder_path': str(self.input_dir_path.absolute()), 'edl_ext': '.yml'}

        with patch.object(sys, 'stdin', StringIO(json.dumps(self.cronicle_json_input))):
            job.process_directory(self.config_path)

        common_expected_post_args = ['http://localhost:3012/api/app/run_event/v1']
        common_expected_post_kwargs = {
            'headers': {'X-API-Key': self.cronicle_json_input['params']['api_key']},
            'json': {'title': 'Process Movie'}
        }

        movie_expected_post_kwargs = common_expected_post_kwargs | {'json': common_expected_post_kwargs['json'] | {'params': EquivalentProcessFileParams({'file_path': str(self.video_path.absolute()), 'edl_ext': '.pending_yml_'})}} 
        mock_post.assert_any_call(*common_expected_post_args, **movie_expected_post_kwargs)

        serie_expected_post_kwargs = common_expected_post_kwargs | {'json': common_expected_post_kwargs['json'] | {'params': EquivalentProcessFileParams({'file_path': str(self.serie_path.absolute()), 'edl_ext': '.pending_yml_'})}}
        mock_post.assert_any_call(*common_expected_post_args, **serie_expected_post_kwargs)

        output = mock_stdout.getvalue()
        self.assertRegex(output, re.compile(r'{"progress": [\d.]+'))
        self.assertRegex(output, re.compile(r'"perf": {"SubmitJobs": [\d.]+'))
        self.assertRegex(output, '{"complete": 1, "code": 0}')

        expected_custom_table_json = json.dumps({
            "table": {
                "title": "Movies to process",
                "header": ["Edl Path", "Job status"],
                "rows": [
                    [self.video_path.name, '🔄️ PROCESSING (http://localhost:3012/#JobDetails?id=23f5c37f)'],
                    [self.serie_path.name, '⏳ ENQUEUED']
                ],
                "caption": "2 tasks."
            }
        })

        self.assertIn(expected_custom_table_json, output)


    def tearDown(self) -> None:
        shutil.rmtree(self.input_dir_path)
        shutil.rmtree(self.output_dir_path)


class EquivalentProcessFileParams:
    def __init__(self, compared_object: dict[str, str]):
        self.compared_object = compared_object
        
    def __eq__(self, other: dict[str, str]) -> bool:
        return other.keys() == self.compared_object.keys() \
            and other['file_path'] == self.compared_object['file_path'] \
            and other['edl_ext'].startswith(self.compared_object['edl_ext'])
    
    def __repr__(self) -> str:
        return repr(self.compared_object)
