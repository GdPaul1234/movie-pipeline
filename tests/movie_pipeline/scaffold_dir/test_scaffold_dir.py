from argparse import Namespace
import shutil
import unittest
from pathlib import Path

from movie_pipeline.commands.scaffold_dir import PathScaffolder, MovieProcessedFileGenerator
from settings import Settings

from movie_pipeline.lib.title_cleaner import TitleCleaner
from movie_pipeline.lib.title_extractor import NaiveTitleExtractor

input_dir_path = Path(__file__).parent.joinpath('in')
video_path = input_dir_path.joinpath('channel 1_Movie Name_2022-11-1601-20.mp4')

sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')

blacklist_path = Path(__file__).parent.parent.joinpath('ressources', 'test_title_re_blacklist.txt')
default_title_cleaner = TitleCleaner(blacklist_path)
default_title_extractor = NaiveTitleExtractor(default_title_cleaner)

output_dir_path = Path(__file__).parent.joinpath('out')
output_dir_movie_path = output_dir_path.joinpath('Films')
output_dir_serie_path = output_dir_path.joinpath('Séries')
backup_dir_path = output_dir_path.joinpath('backup')

config_path = Path(__file__).parent.joinpath('test_config.env')
options = Namespace()
setattr(options, 'config_path', config_path)
lazy_config = lambda: Settings(_env_file=options.config_path, _env_file_encoding='utf-8') # type: ignore


class TestScaffoldDir(unittest.TestCase):
    def setUp(self) -> None:
        input_dir_path.mkdir()
        shutil.copyfile(sample_video_path, video_path)

        output_dir_movie_path.mkdir(parents=True)
        output_dir_serie_path.mkdir(parents=True)
        backup_dir_path.mkdir()

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
