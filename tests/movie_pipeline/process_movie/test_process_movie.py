import shutil
import unittest
from collections import deque
from pathlib import Path

from movie_pipeline.services.movie_file_processor.core import MovieFileProcessor

from ..concerns import (
    copy_files, create_output_movies_directories, get_output_movies_directories, lazy_load_config_file,
    get_movie_edl_file_content, get_serie_edl_file_content
)


class TestProcessMovie(unittest.TestCase):
    def setUp(self) -> None:
        self.input_dir_path = Path(__file__).parent.joinpath('in')
        self.video_path = self.input_dir_path.joinpath('channel 1_Movie Name_2022-11-1601-20.mp4')
        self.serie_path = self.input_dir_path.joinpath('channel 1_Serie Name S01E23_2022-11-1601-20.mp4')
        
        self.output_dir_path, self.output_dir_movie_path, self.output_dir_serie_path, self.backup_dir_path = get_output_movies_directories(Path(__file__).parent)
        self.lazy_config = lazy_load_config_file(Path(__file__).parent)

        sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')
        copy_files([
            {'source': sample_video_path, 'destination': self.video_path},
            {'source': sample_video_path, 'destination': self.serie_path}
        ])

        create_output_movies_directories(Path(__file__).parent)

    def test_segments(self):
        edl_path = self.video_path.with_suffix('.mp4.yml')
        edl_path.write_text(get_movie_edl_file_content(), encoding='utf-8')
        movie_processor = MovieFileProcessor(edl_path, self.lazy_config())

        expected_segments = [(3.37, 5.96), (10.52, 18.2), (20.32, 25.08)]
        self.assertEqual(expected_segments, movie_processor.segments)

    def test_segments_total_seconds(self):
        edl_path = self.video_path.with_suffix('.mp4.yml')
        edl_path.write_text(get_movie_edl_file_content(), encoding='utf-8')
        movie_processor = MovieFileProcessor(edl_path, self.lazy_config())

        self.assertAlmostEqual(15.03, movie_processor.movie_segments.total_seconds)

    def test_movie_process(self):
        edl_path = self.video_path.with_suffix('.mp4.yml')
        edl_path.write_text(get_movie_edl_file_content(), encoding='utf-8')
        movie_processor = MovieFileProcessor(edl_path, self.lazy_config())
    
        deque(movie_processor.process_with_progress(), maxlen=0)

        self.assertFalse(self.video_path.exists())
        self.assertTrue(self.output_dir_movie_path.joinpath('Movie Name', 'Movie Name.mp4').exists())
        self.assertTrue(self.backup_dir_path.joinpath('Movie Name', 'channel 1_Movie Name_2022-11-1601-20.mp4').exists())
        self.assertTrue(self.backup_dir_path.joinpath('Movie Name', 'channel 1_Movie Name_2022-11-1601-20.mp4.yml').exists())

    def test_movie_skip_backup_process(self):
        edl_path = self.video_path.with_suffix('.mp4.yml')
        edl_path.write_text(get_movie_edl_file_content(skip_backup=True), encoding='utf-8')
        movie_processor = MovieFileProcessor(edl_path, self.lazy_config())

        deque(movie_processor.process_with_progress(), maxlen=0)

        self.assertTrue(self.video_path.exists())
        self.assertTrue(edl_path.with_suffix('.yml.done').exists())
        self.assertTrue(self.output_dir_movie_path.joinpath('Movie Name', 'Movie Name.mp4').exists())
        self.assertFalse(self.backup_dir_path.joinpath('Movie Name').exists())

    def test_serie_process(self):
        edl_path = self.serie_path.with_suffix('.mp4.yml')
        edl_path.write_text(get_serie_edl_file_content(), encoding='utf-8')
        movie_processor = MovieFileProcessor(edl_path, self.lazy_config())

        deque(movie_processor.process_with_progress(), maxlen=0)

        self.assertFalse(self.serie_path.exists())
        self.assertFalse(edl_path.exists())
        self.assertTrue(self.output_dir_serie_path.joinpath('Serie Name', 'Saison 1', 'Serie Name S01E23.mp4'))

    def tearDown(self) -> None:
        shutil.rmtree(self.input_dir_path)
        shutil.rmtree(self.output_dir_path)
