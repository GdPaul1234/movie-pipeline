from collections import deque
from pathlib import Path
import re
import shutil
import textwrap
import unittest

import ffmpeg

from movie_pipeline.lib.util import total_movie_duration
from movie_pipeline.services.movie_file_processor.core import MovieFileProcessor
from movie_pipeline.services.movie_file_processor.movie_file_processor_step import BaseStepInterruptedError

from ..concerns import copy_files, get_output_movies_directories, lazy_load_config_file

input_dir_path = Path(__file__).parent / 'in'
video_path = input_dir_path / 'channel 1_Movie Name_2022-11-1601-20.mp4'
serie_path = input_dir_path / 'channel 1_Serie Name S01E23_2022-11-1601-20.mp4'

output_dir_path, output_dir_movie_path, output_dir_serie_path, backup_dir_path = \
    get_output_movies_directories(Path(__file__).parent)

serie_output_dir_path = output_dir_serie_path / 'Serie Name' / 'Saison 1'
other_output_serie_file_path = serie_output_dir_path / 'Serie Name S01E24.mp4'
video_output_movie_dir_path = output_dir_movie_path / 'Movie Name'

lazy_config = lazy_load_config_file(Path(__file__).parent)

class TestRecoverFailedMovie(unittest.TestCase):
    def setUp(self) -> None:
        sample_video_path = Path(__file__).parent.parent / 'ressources' / 'counter-30s.mp4'
        copy_files([
            {'source': sample_video_path, 'destination': video_path},
            {'source': sample_video_path, 'destination': serie_path},
            {'source': sample_video_path, 'destination': other_output_serie_file_path}
        ])

        self.edl_serie_path = serie_path.with_suffix('.mp4.yml')
        self.edl_serie_path.write_text(textwrap.dedent('''\
            filename: Serie Name S01E23.mp4
            segments: 00:00:03.370-00:00:05.960,00:00:10.520-00:00:18.200,00:00:20.320-00:00:25.080,
        '''), encoding='utf-8')

        self.edl_video_path = video_path.with_suffix('.mp4.yml')
        self.edl_video_path.write_text(textwrap.dedent('''\
            filename: Movie Name.mp4
            segments: 00:00:03.370-00:00:05.960,00:00:10.520-00:00:18.200,00:00:20.320-00:00:25.080,
        '''), encoding='utf-8')

        output_dir_movie_path.mkdir(parents=True)
        backup_dir_path.mkdir(parents=True)

    def test_recover_failed_movie(self):
        output_video_file_path = video_output_movie_dir_path / 'Movie Name.mp4'
        video_output_movie_dir_path.mkdir(parents=True)
        output_video_file_path.touch()

        self.assertEqual(1, len(list(video_output_movie_dir_path.iterdir())))

        with self.assertRaises(ffmpeg.Error):
            total_movie_duration(output_video_file_path)

        movie_processor = MovieFileProcessor(self.edl_video_path, lazy_config())
        deque(movie_processor.process_with_progress(), maxlen=0)

        self.assertFalse(video_path.exists())
        self.assertTrue(output_video_file_path.exists())
        self.assertEqual(1, len(list(output_dir_movie_path.iterdir())))
        self.assertAlmostEqual(15.03, total_movie_duration(output_video_file_path), places=1)

    def test_recover_failed_serie(self):
        output_serie_file_path = serie_output_dir_path / 'Serie Name S01E23.mp4'
        output_serie_file_path.touch()

        self.assertEqual(2, len(list(serie_output_dir_path.iterdir())))

        with self.assertRaises(ffmpeg.Error):
            total_movie_duration(output_serie_file_path)

        movie_processor = MovieFileProcessor(self.edl_serie_path, lazy_config())
        deque(movie_processor.process_with_progress(), maxlen=0)

        self.assertFalse(serie_path.exists())
        self.assertFalse(self.edl_serie_path.exists())

        self.assertTrue(output_serie_file_path.exists())
        self.assertEqual(2, len(list(serie_output_dir_path.iterdir())))
        self.assertAlmostEqual(15.03, total_movie_duration(output_serie_file_path), places=1)

    def test_pass_already_processed_movie(self):
        output_video_file_path = video_output_movie_dir_path / 'Movie Name.mp4'
        copy_files([
            {"source": self.edl_video_path, "destination": input_dir_path / 'backuped_video_edl.yml'},
            {"source": video_path, "destination": input_dir_path / 'backuped_video.mp4'}
        ])

        movie_processor = MovieFileProcessor(self.edl_video_path, lazy_config())
        deque(movie_processor.process_with_progress(), maxlen=0)
        self.assertAlmostEqual(15.03, total_movie_duration(output_video_file_path), places=1)

        (input_dir_path / 'backuped_video_edl.yml').rename(self.edl_video_path)
        (input_dir_path / 'backuped_video.mp4').rename(video_path)

        with self.assertRaisesRegex(BaseStepInterruptedError, re.compile(r'Valid ".+" already exists')):
            deque(movie_processor.process_with_progress(), maxlen=0)

        self.assertTrue(video_path.exists())
        self.assertTrue(self.edl_video_path.with_suffix('.yml.done').exists())

        self.assertTrue(output_video_file_path.exists())
        self.assertEqual(1, len(list(output_dir_movie_path.iterdir())))
        self.assertAlmostEqual(15.03, total_movie_duration(output_video_file_path), places=1)

    def test_pass_already_processed_serie(self):
        output_serie_file_path = serie_output_dir_path / 'Serie Name S01E23.mp4'
        copy_files([
            {"source": self.edl_serie_path, "destination": input_dir_path / 'backuped_serie_edl.yml'},
            {"source": serie_path, "destination": input_dir_path / 'backuped_serie.mp4'}
        ])

        movie_processor = MovieFileProcessor(self.edl_serie_path, lazy_config())
        deque(movie_processor.process_with_progress(), maxlen=0)
        self.assertAlmostEqual(15.03, total_movie_duration(output_serie_file_path), places=1)

        (input_dir_path / 'backuped_serie_edl.yml').rename(self.edl_serie_path)
        (input_dir_path / 'backuped_serie.mp4').rename(serie_path)

        with self.assertRaisesRegex(BaseStepInterruptedError, re.compile(r'Valid ".+" already exists')):
            deque(movie_processor.process_with_progress(), maxlen=0)

        self.assertTrue(serie_path.exists())
        self.assertTrue(self.edl_serie_path.with_suffix('.yml.done').exists())

        self.assertTrue(output_serie_file_path.exists())
        self.assertEqual(2, len(list(serie_output_dir_path.iterdir())))
        self.assertAlmostEqual(15.03, total_movie_duration(output_serie_file_path), places=1)

    def tearDown(self) -> None:
        shutil.rmtree(input_dir_path)
        shutil.rmtree(output_dir_path)
