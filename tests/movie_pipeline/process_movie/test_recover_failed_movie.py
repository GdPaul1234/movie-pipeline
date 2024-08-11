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

from ..concerns import copy_files, get_output_movies_directories, lazy_load_config_file, get_movie_edl_file_content, get_serie_edl_file_content


class TestRecoverFailedMovie(unittest.TestCase):
    def setUp(self) -> None:
        self.input_dir_path = Path(__file__).parent / 'in'
        self.video_path = self.input_dir_path / 'channel 1_Movie Name_2022-11-1601-20.mp4'
        self.serie_path = self.input_dir_path / 'channel 1_Serie Name S01E23_2022-11-1601-20.mp4'
        
        self.output_dir_path, self.output_dir_movie_path, output_dir_serie_path, backup_dir_path = get_output_movies_directories(Path(__file__).parent)
        self.serie_output_dir_path = output_dir_serie_path / 'Serie Name' / 'Saison 1'
        other_output_serie_file_path = self.serie_output_dir_path / 'Serie Name S01E24.mp4'
        self.video_output_movie_dir_path = self.output_dir_movie_path / 'Movie Name'
        self.lazy_config = lazy_load_config_file(Path(__file__).parent)

        sample_video_path = Path(__file__).parent.parent / 'ressources' / 'counter-30s.mp4'
        copy_files([
            {'source': sample_video_path, 'destination': self.video_path},
            {'source': sample_video_path, 'destination': self.serie_path},
            {'source': sample_video_path, 'destination': other_output_serie_file_path}
        ])

        self.edl_serie_path = self.serie_path.with_suffix('.mp4.yml')
        self.edl_serie_path.write_text(get_serie_edl_file_content(), encoding='utf-8')

        self.edl_video_path = self.video_path.with_suffix('.mp4.yml')
        self.edl_video_path.write_text(get_movie_edl_file_content(), encoding='utf-8')

        self.output_dir_movie_path.mkdir(parents=True)
        backup_dir_path.mkdir(parents=True)

    def test_recover_failed_movie(self):
        output_video_file_path = self.video_output_movie_dir_path / 'Movie Name.mp4'
        self.video_output_movie_dir_path.mkdir(parents=True)
        output_video_file_path.touch()

        self.assertEqual(1, len(list(self.video_output_movie_dir_path.iterdir())))

        with self.assertRaises(ffmpeg.Error):
            total_movie_duration(output_video_file_path)

        movie_processor = MovieFileProcessor(self.edl_video_path, self.lazy_config())
        deque(movie_processor.process_with_progress(), maxlen=0)

        self.assertFalse(self.video_path.exists())
        self.assertTrue(output_video_file_path.exists())
        self.assertEqual(1, len(list(self.output_dir_movie_path.iterdir())))
        self.assertAlmostEqual(15.03, total_movie_duration(output_video_file_path), places=1)

    def test_recover_failed_serie(self):
        output_serie_file_path = self.serie_output_dir_path / 'Serie Name S01E23.mp4'
        output_serie_file_path.touch()

        self.assertEqual(2, len(list(self.serie_output_dir_path.iterdir())))

        with self.assertRaises(ffmpeg.Error):
            total_movie_duration(output_serie_file_path)

        movie_processor = MovieFileProcessor(self.edl_serie_path, self.lazy_config())
        deque(movie_processor.process_with_progress(), maxlen=0)

        self.assertFalse(self.serie_path.exists())
        self.assertFalse(self.edl_serie_path.exists())

        self.assertTrue(output_serie_file_path.exists())
        self.assertEqual(2, len(list(self.serie_output_dir_path.iterdir())))
        self.assertAlmostEqual(15.03, total_movie_duration(output_serie_file_path), places=1)

    def test_pass_already_processed_movie(self):
        output_video_file_path = self.video_output_movie_dir_path / 'Movie Name.mp4'
        copy_files([
            {"source": self.edl_video_path, "destination": self.input_dir_path / 'backuped_video_edl.yml'},
            {"source": self.video_path, "destination": self.input_dir_path / 'backuped_video.mp4'}
        ])

        movie_processor = MovieFileProcessor(self.edl_video_path, self.lazy_config())
        deque(movie_processor.process_with_progress(), maxlen=0)
        self.assertAlmostEqual(15.03, total_movie_duration(output_video_file_path), places=1)

        (self.input_dir_path / 'backuped_video_edl.yml').rename(self.edl_video_path)
        (self.input_dir_path / 'backuped_video.mp4').rename(self.video_path)

        with self.assertRaisesRegex(BaseStepInterruptedError, re.compile(r'Valid ".+" already exists')):
            deque(movie_processor.process_with_progress(), maxlen=0)

        self.assertTrue(self.video_path.exists())
        self.assertTrue(self.edl_video_path.with_suffix('.yml.done').exists())

        self.assertTrue(output_video_file_path.exists())
        self.assertEqual(1, len(list(self.output_dir_movie_path.iterdir())))
        self.assertAlmostEqual(15.03, total_movie_duration(output_video_file_path), places=1)

    def test_pass_already_processed_serie(self):
        output_serie_file_path = self.serie_output_dir_path / 'Serie Name S01E23.mp4'
        copy_files([
            {"source": self.edl_serie_path, "destination": self.input_dir_path / 'backuped_serie_edl.yml'},
            {"source": self.serie_path, "destination": self.input_dir_path / 'backuped_serie.mp4'}
        ])

        movie_processor = MovieFileProcessor(self.edl_serie_path, self.lazy_config())
        deque(movie_processor.process_with_progress(), maxlen=0)
        self.assertAlmostEqual(15.03, total_movie_duration(output_serie_file_path), places=1)

        (self.input_dir_path / 'backuped_serie_edl.yml').rename(self.edl_serie_path)
        (self.input_dir_path / 'backuped_serie.mp4').rename(self.serie_path)

        with self.assertRaisesRegex(BaseStepInterruptedError, re.compile(r'Valid ".+" already exists')):
            deque(movie_processor.process_with_progress(), maxlen=0)

        self.assertTrue(self.serie_path.exists())
        self.assertTrue(self.edl_serie_path.with_suffix('.yml.done').exists())

        self.assertTrue(output_serie_file_path.exists())
        self.assertEqual(2, len(list(self.serie_output_dir_path.iterdir())))
        self.assertAlmostEqual(15.03, total_movie_duration(output_serie_file_path), places=1)

    def tearDown(self) -> None:
        shutil.rmtree(self.input_dir_path)
        shutil.rmtree(self.output_dir_path)
