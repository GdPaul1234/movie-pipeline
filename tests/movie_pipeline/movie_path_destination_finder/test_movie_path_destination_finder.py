import shutil
import unittest
from pathlib import Path

from movie_pipeline.lib.movie_path_destination_finder import \
    MoviePathDestinationFinder
from movie_pipeline.models.movie_file import LegacyMovieFile

from ..concerns import (copy_files, create_output_movies_directories,
                        get_output_movies_directories, lazy_load_config_file)

input_dir_path = Path(__file__).parent.joinpath('in')
video_path = input_dir_path.joinpath('channel 1_Movie Name_2022-11-1601-20.mp4')
serie_path = input_dir_path.joinpath('channel 1_Serie Name S01E23_2022-11-1601-20.mp4')

output_dir_path, output_dir_movie_path, output_dir_serie_path, backup_dir_path = \
    get_output_movies_directories(Path(__file__).parent)

lazy_config = lazy_load_config_file(Path(__file__).parent)

class TestMoviePathDestinationFinder(unittest.TestCase):
    def setUp(self) -> None:
        sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')
        copy_files([
            {'source': sample_video_path, 'destination': video_path},
            {'source': sample_video_path, 'destination': serie_path}
        ])

        create_output_movies_directories(Path(__file__).parent)

    def test_movie_resolve_destination(self):
        finder = MoviePathDestinationFinder(LegacyMovieFile('Movie Name.mp4'), lazy_config())

        self.assertEqual(
            output_dir_movie_path.joinpath('Movie Name'),
            finder.resolve_destination().resolve()
        )

    def test_serie_resolve_destination(self):
        finder = MoviePathDestinationFinder(LegacyMovieFile('Serie Name S01E23.mp4'), lazy_config())

        self.assertEqual(
            output_dir_serie_path.joinpath('Serie Name', 'Saison 1'),
            finder.resolve_destination().resolve()
        )

    def test_existing_serie_resolve_destination(self):
        finder = MoviePathDestinationFinder(LegacyMovieFile('Other Serie Name S02E34.mp4'), lazy_config())
        serie_folder = output_dir_serie_path.joinpath('Other Serie Name (2022)', 'Saison 2')
        serie_folder.mkdir(parents=True)

        self.assertEqual(serie_folder, finder.resolve_destination().resolve())

    def tearDown(self) -> None:
        shutil.rmtree(input_dir_path)
        shutil.rmtree(output_dir_path)
