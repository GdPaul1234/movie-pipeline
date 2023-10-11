import shutil
import unittest
from pathlib import Path

from movie_pipeline.services.edl_scaffolder import PathScaffolder
from movie_pipeline.lib.title_extractor.title_cleaner import TitleCleaner
from movie_pipeline.lib.title_extractor.title_extractor import NaiveTitleExtractor
from movie_pipeline.services.edl_scaffolder import MovieProcessedFileGenerator

from ..concerns import get_output_movies_directories, create_output_movies_directories, lazy_load_config_file

input_dir_path = Path(__file__).parent.joinpath('in')
video_path = input_dir_path.joinpath('channel 1_Movie Name_2022-11-1601-20.mp4')

sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')

blacklist_path = Path(__file__).parent.parent.joinpath('ressources', 'test_title_re_blacklist.txt')
default_title_cleaner = TitleCleaner(blacklist_path)
default_title_extractor = NaiveTitleExtractor(default_title_cleaner)

output_dir_path, output_dir_movie_path, output_dir_serie_path, backup_dir_path = \
    get_output_movies_directories(Path(__file__).parent)

lazy_config = lazy_load_config_file(Path(__file__).parent)

class TestScaffoldDir(unittest.TestCase):
    def setUp(self) -> None:
        input_dir_path.mkdir()
        shutil.copyfile(sample_video_path, video_path)

        create_output_movies_directories(Path(__file__).parent)

    def test_extract_title(self):
        edl_template = MovieProcessedFileGenerator(video_path, default_title_extractor)
        self.assertEqual('Movie Name', edl_template.extract_title())

    def test_generate_edl_file(self):
        edl_template = MovieProcessedFileGenerator(video_path, default_title_extractor)

        edl_template.generate()

        expected_content = 'filename: Movie Name.mp4\nsegments: INSERT_SEGMENTS_HERE\n'
        actual_content = video_path.with_suffix('.mp4.yml.txt').read_text()
        self.assertEqual(expected_content, actual_content)

    def test_scaffold_dir(self):
        shutil.copyfile(sample_video_path, video_path.with_suffix('.ts'))

        self.assertTrue(PathScaffolder(input_dir_path, lazy_config()).scaffold())
        self.assertTrue(video_path.with_suffix('.ts.yml.txt'))

    def test_no_scaffold_dir_when_already_created(self):
        shutil.copyfile(sample_video_path, video_path.with_suffix('.ts'))
        video_path.with_suffix('.ts.yml').write_text("DON'T EDIT ME!")

        self.assertFalse(PathScaffolder(input_dir_path, lazy_config()).scaffold())
        self.assertFalse(video_path.with_suffix('.ts.yml.txt').exists())


    def tearDown(self) -> None:
        shutil.rmtree(input_dir_path)
        shutil.rmtree(output_dir_path)
