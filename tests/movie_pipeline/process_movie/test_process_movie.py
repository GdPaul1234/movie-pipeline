import shutil
import textwrap
import unittest
from pathlib import Path

from rich.progress import Progress

from movie_pipeline.commands.process_movie import MovieFileProcessor

from ..concerns import get_output_movies_directories, create_output_movies_directories, lazy_load_config_file

input_dir_path = Path(__file__).parent.joinpath('in')
video_path = input_dir_path.joinpath('channel 1_Movie Name_2022-11-1601-20.mp4')
serie_path = input_dir_path.joinpath('channel 1_Serie Name S01E23_2022-11-1601-20.mp4')

output_dir_path, output_dir_movie_path, output_dir_serie_path, backup_dir_path = \
    get_output_movies_directories(Path(__file__).parent)

lazy_config = lazy_load_config_file(Path(__file__).parent)


class TestProcessMovie(unittest.TestCase):
    def setUp(self) -> None:
        input_dir_path.mkdir()
        sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')
        shutil.copyfile(sample_video_path, video_path)
        shutil.copyfile(sample_video_path, serie_path)

        create_output_movies_directories(Path(__file__).parent)

    def test_segments(self):
        edl_path = video_path.with_suffix('.mp4.yml')
        edl_path.write_text(textwrap.dedent('''\
            filename: Movie Name.mp4
            segments: 00:00:03.370-00:00:05.960,00:00:10.520-00:00:18.200,00:00:20.320-00:00:25.080,
        '''), encoding='utf-8')

        with Progress() as progress:
            movie_processor = MovieFileProcessor(edl_path, progress, lazy_config())

        expected_segments = [(3.37, 5.96), (10.52, 18.2), (20.32, 25.08)]
        self.assertEqual(expected_segments, movie_processor._segments)

    def test_segments_total_seconds(self):
        edl_path = video_path.with_suffix('.mp4.yml')
        edl_path.write_text(textwrap.dedent('''\
            filename: Movie Name.mp4
            segments: 00:00:03.370-00:00:05.960,00:00:10.520-00:00:18.200,00:00:20.320-00:00:25.080,
        '''), encoding='utf-8')

        with Progress() as progress:
            movie_processor = MovieFileProcessor(edl_path, progress, lazy_config())

            self.assertAlmostEqual(15.03, movie_processor._movie_segments.total_seconds)

    def test_movie_process(self):
        edl_path = video_path.with_suffix('.mp4.yml')
        edl_path.write_text(textwrap.dedent('''\
            filename: Movie Name.mp4
            segments: 00:00:03.370-00:00:05.960,00:00:10.520-00:00:18.200,00:00:20.320-00:00:25.080,
        '''), encoding='utf-8')

        with Progress() as progress:
            movie_processor = MovieFileProcessor(edl_path, progress, lazy_config())
            movie_processor.process()

        self.assertFalse(video_path.exists())
        self.assertTrue(output_dir_movie_path.joinpath('Movie Name', 'Movie Name.mp4').exists())
        self.assertTrue(backup_dir_path.joinpath('Movie Name', 'channel 1_Movie Name_2022-11-1601-20.mp4').exists())
        self.assertTrue(backup_dir_path.joinpath('Movie Name', 'channel 1_Movie Name_2022-11-1601-20.mp4.yml').exists())

    def test_movie_skip_backup_process(self):
        edl_path = video_path.with_suffix('.mp4.yml')
        edl_path.write_text(textwrap.dedent('''\
            filename: Movie Name.mp4
            segments: 00:00:03.370-00:00:05.960,00:00:10.520-00:00:18.200,00:00:20.320-00:00:25.080,
            skip_backup: yes
        '''), encoding='utf-8')

        with Progress() as progress:
            movie_processor = MovieFileProcessor(edl_path, progress, lazy_config())
            movie_processor.process()

        self.assertTrue(video_path.exists())
        self.assertTrue(edl_path.with_suffix('.yml.done').exists())
        self.assertTrue(output_dir_movie_path.joinpath('Movie Name', 'Movie Name.mp4').exists())
        self.assertFalse(backup_dir_path.joinpath('Movie Name').exists())

    def test_serie_process(self):
        edl_path = serie_path.with_suffix('.mp4.yml')
        edl_path.write_text(textwrap.dedent('''\
            filename: Serie Name S01E23.mp4
            segments: 00:00:03.370-00:00:05.960,00:00:10.520-00:00:18.200,00:00:20.320-00:00:25.080,
        '''), encoding='utf-8')

        with Progress() as progress:
            movie_processor = MovieFileProcessor(edl_path, progress, lazy_config())
            movie_processor.process()

        self.assertFalse(serie_path.exists())
        self.assertFalse(edl_path.exists())
        self.assertTrue(output_dir_serie_path.joinpath('Serie Name', 'Saison 1', 'Serie Name S01E23.mp4'))

    def tearDown(self) -> None:
        shutil.rmtree(input_dir_path)
        shutil.rmtree(output_dir_path)
