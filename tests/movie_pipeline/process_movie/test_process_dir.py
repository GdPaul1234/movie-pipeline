import shutil
import textwrap
import unittest
from pathlib import Path

from movie_pipeline.services.movie_file_processor_folder_runner import \
    MovieFileProcessorFolderRunner
from movie_pipeline.lib.ui_factory import ProgressUIFactory

from ..concerns import (copy_files, create_output_movies_directories,
                        get_output_movies_directories, lazy_load_config_file)

input_dir_path = Path(__file__).parent.joinpath('in')
video_path = input_dir_path.joinpath('channel 1_Movie Name_2022-11-1601-20.mp4')
serie_path = input_dir_path.joinpath('channel 1_Serie Name S01E23_2022-11-1601-20.mp4')

output_dir_path, output_dir_movie_path, output_dir_serie_path, backup_dir_path = \
    get_output_movies_directories(Path(__file__).parent)

lazy_config = lazy_load_config_file(Path(__file__).parent)

class TestProcessDir(unittest.TestCase):
    def setUp(self) -> None:
        sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')
        copy_files([
            {'source': sample_video_path, 'destination': video_path},
            {'source': sample_video_path, 'destination': serie_path}
        ])

        create_output_movies_directories(Path(__file__).parent)

    def test_custom_ext_process(self):
        edl_serie_path = serie_path.with_suffix('.mp4.custom_ext')
        edl_serie_path.write_text(textwrap.dedent('''\
            filename: Serie Name S01E23.mp4
            segments: 00:00:03.370-00:00:05.960,00:00:10.520-00:00:18.200,00:00:20.320-00:00:25.080,
        '''), encoding='utf-8')

        progress_listener = ProgressUIFactory.create_process_listener()
        MovieFileProcessorFolderRunner(input_dir_path, '.custom_ext', progress_listener, lazy_config()).process_directory()

        self.assertFalse(serie_path.exists())
        self.assertFalse(edl_serie_path.exists())
        self.assertTrue(output_dir_serie_path.joinpath('Serie Name', 'Saison 1', 'Serie Name S01E23.mp4'))

    def test_custom_ext_ignore_process(self):
        edl_video_path = video_path.with_suffix('.mp4.yml')
        edl_video_path.write_text(textwrap.dedent('''\
            filename: Movie Name.mp4
            segments: 00:00:03.370-00:00:05.960,00:00:10.520-00:00:18.200,00:00:20.320-00:00:25.080,
        '''), encoding='utf-8')

        progress_listener = ProgressUIFactory.create_process_listener()
        MovieFileProcessorFolderRunner(input_dir_path, '.custom_ext', progress_listener, lazy_config()).process_directory()

        self.assertTrue(video_path.exists())
        self.assertTrue(edl_video_path.exists())

    def tearDown(self) -> None:
        shutil.rmtree(input_dir_path)
        shutil.rmtree(output_dir_path)
