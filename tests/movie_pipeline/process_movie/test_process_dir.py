import shutil
import unittest
from pathlib import Path

from movie_pipeline.services.movie_file_processor.runner.folder.folder_runner import MovieFileProcessorFolderRunner
from movie_pipeline.lib.ui_factory import ProgressUIFactory

from ..concerns import (
    copy_files, create_output_movies_directories, get_output_movies_directories, lazy_load_config_file,
    get_movie_edl_file_content, get_serie_edl_file_content
)


class TestProcessDir(unittest.TestCase):
    def setUp(self) -> None:
        self.input_dir_path = Path(__file__).parent.joinpath('in')
        self.video_path = self.input_dir_path.joinpath('channel 1_Movie Name_2022-11-1601-20.mp4')
        self.serie_path = self.input_dir_path.joinpath('channel 1_Serie Name S01E23_2022-11-1601-20.mp4')
        
        self.output_dir_path, _, self.output_dir_serie_path, _ = get_output_movies_directories(Path(__file__).parent)
        self.lazy_config = lazy_load_config_file(Path(__file__).parent)

        sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')
        copy_files([
            {'source': sample_video_path, 'destination': self.video_path},
            {'source': sample_video_path, 'destination': self.serie_path}
        ])

        self.progress_listener = ProgressUIFactory.create_process_listener()

        create_output_movies_directories(Path(__file__).parent)

    def test_custom_ext_process(self):
        edl_serie_path = self.serie_path.with_suffix('.mp4.custom_ext')
        edl_serie_path.write_text(get_serie_edl_file_content(), encoding='utf-8')

        MovieFileProcessorFolderRunner(self.input_dir_path, '.custom_ext', self.progress_listener, self.lazy_config()).process_directory()

        self.assertFalse(self.serie_path.exists())
        self.assertFalse(edl_serie_path.exists())
        self.assertTrue(self.output_dir_serie_path.joinpath('Serie Name', 'Saison 1', 'Serie Name S01E23.mp4'))

    def test_custom_ext_ignore_process(self):
        edl_video_path = self.video_path.with_suffix('.mp4.yml')
        edl_video_path.write_text(get_movie_edl_file_content(), encoding='utf-8')

        MovieFileProcessorFolderRunner(self.input_dir_path, '.custom_ext', self.progress_listener, self.lazy_config()).process_directory()

        self.assertTrue(self.video_path.exists())
        self.assertTrue(edl_video_path.exists())

    def tearDown(self) -> None:
        shutil.rmtree(self.input_dir_path)
        shutil.rmtree(self.output_dir_path)
