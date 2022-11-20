from argparse import Namespace
from pathlib import Path
import shutil
import textwrap
import unittest

from config_loader import ConfigLoader
from process_movie import MovieFileProcessorFolderRunner

input_dir_path = Path(__file__).parent.joinpath('in')
video_path = input_dir_path.joinpath('channel 1_Movie Name_2022-11-1601-20.mp4')
serie_path = input_dir_path.joinpath('channel 1_Serie Name S01E23_2022-11-1601-20.mp4')

output_dir_path = Path(__file__).parent.joinpath('out')
output_dir_movie_path = output_dir_path.joinpath('Films')
output_dir_serie_path = output_dir_path.joinpath('Séries')
backup_dir_path = output_dir_path.joinpath('backup')

config_path = Path(__file__).parent.joinpath('test_config.ini')
options = Namespace()
setattr(options, 'config_path', config_path)
config = ConfigLoader(options).config


class TestProcessDir(unittest.TestCase):
    def setUp(self) -> None:
        input_dir_path.mkdir()
        sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')
        shutil.copyfile(sample_video_path, video_path)
        shutil.copyfile(sample_video_path, serie_path)

        output_dir_movie_path.mkdir(parents=True)
        output_dir_serie_path.mkdir(parents=True)
        backup_dir_path.mkdir()

    def test_custom_ext_process(self):
        edl_serie_path = serie_path.with_suffix('.mp4.custom_ext')
        edl_serie_path.write_text(textwrap.dedent('''\
            filename: Serie Name S01E23.mp4
            segments: 00:00:03.370-00:00:05.960,00:00:10.520-00:00:18.200,00:00:20.320-00:00:25.080,
        '''), encoding='utf-8')

        MovieFileProcessorFolderRunner.process_directory(input_dir_path, '.custom_ext', config)

        self.assertFalse(serie_path.exists())
        self.assertFalse(edl_serie_path.exists())
        self.assertTrue(output_dir_serie_path.joinpath('Serie Name', 'Saison 1', 'Serie Name S01E23.mp4'))

    def test_custom_ext_ignore_process(self):
        edl_video_path = video_path.with_suffix('.mp4.yml')
        edl_video_path.write_text(textwrap.dedent('''\
            filename: Movie Name.mp4
            segments: 00:00:03.370-00:00:05.960,00:00:10.520-00:00:18.200,00:00:20.320-00:00:25.080,
        '''), encoding='utf-8')

        MovieFileProcessorFolderRunner.process_directory(input_dir_path, '.custom_ext', config)

        self.assertTrue(video_path.exists())
        self.assertTrue(edl_video_path.exists())

    def tearDown(self) -> None:
        shutil.rmtree(input_dir_path)
        shutil.rmtree(output_dir_path)
