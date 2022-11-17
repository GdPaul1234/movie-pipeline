from argparse import Namespace
import shutil
import unittest
from pathlib import Path

from movie_file import LegacyMovieFile
from movie_path_destination_finder import MoviePathDestinationFinder
from config_loader import ConfigLoader

input_dir_path = Path(__file__).parent.joinpath('in')
output_dir_path = Path(__file__).parent.joinpath('out')

output_dir_movie_path = output_dir_path.joinpath('Films')
video_path = input_dir_path.joinpath('channel 1_Movie Name_2022-11-1601-20.mp4')

output_dir_serie_path = output_dir_path.joinpath('Séries')
serie_path = input_dir_path.joinpath('channel 1_Serie Name S01E23_2022-11-1601-20.mp4')

config_path = Path(__file__).parent.joinpath('config.ini')
options = Namespace()
setattr(options, 'config_path', config_path)
config = ConfigLoader(options).config

class TestMoviePathDestinationFinder(unittest.TestCase):
    def setUp(self) -> None:
        input_dir_path.mkdir()
        sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')
        shutil.copyfile(sample_video_path, video_path)
        shutil.copyfile(sample_video_path, serie_path)

        output_dir_movie_path.mkdir(parents=True)
        output_dir_serie_path.mkdir(parents=True)

    def test_movie_resolve_destination(self):
        finder = MoviePathDestinationFinder(LegacyMovieFile('Movie Name.mp4'), config)

        self.assertEqual(
            output_dir_movie_path.joinpath('Movie Name'),
            finder.resolve_destination().resolve()
        )

    def test_serie_resolve_destination(self):
        finder = MoviePathDestinationFinder(LegacyMovieFile('Serie Name S01E23.mp4'), config)

        self.assertEqual(
            output_dir_serie_path.joinpath('Serie Name', 'Saison 1'),
            finder.resolve_destination().resolve()
        )

    def test_existing_serie_resolve_destination(self):
        finder = MoviePathDestinationFinder(LegacyMovieFile('Other Serie Name S02E34.mp4'), config)
        serie_folder = output_dir_serie_path.joinpath('Other Serie Name (2022)', 'Saison 2')
        serie_folder.mkdir(parents=True)

        self.assertEqual(serie_folder, finder.resolve_destination().resolve())

    def tearDown(self) -> None:
        shutil.rmtree(input_dir_path)
        shutil.rmtree(output_dir_path)
