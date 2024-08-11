import shutil
import textwrap
import unittest
from pathlib import Path

from rich.tree import Tree

from movie_pipeline.services.movie_file_processor.runner.folder.folder_runner import MovieFileProcessorFolderRunner
from movie_pipeline.lib.ui_factory import ProgressUIFactory

from ..concerns import get_output_movies_directories, create_output_movies_directories, lazy_load_config_file


class TestThreadedProcessDir(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir_path, self.output_dir_movie_path, _, self.backup_dir_path = get_output_movies_directories(Path(__file__).parent)
        self.lazy_config = lazy_load_config_file(Path(__file__).parent)

        self.input_dir_path = Path(__file__).parent / 'in'
        self.input_dir_path.mkdir()
        ressources_path = Path(__file__).parent.parent / 'ressources'

        for video in ressources_path.glob('*.mp4'):
            # create video file
            video_path = self.input_dir_path / f'channel 1_{video.stem}_2022-11-291526.mp4'
            shutil.copyfile(video, video_path)

            # create edl
            edl_path = video_path.with_suffix('.mp4.yml')
            edl_path.write_text(textwrap.dedent(f'''\
                filename: {video.stem}.mp4
                segments: 00:00:02.370-00:00:04.960,
            '''), encoding='utf-8')

        create_output_movies_directories(Path(__file__).parent)

        progress_listener = ProgressUIFactory.create_process_listener()
        self.folder_processor = MovieFileProcessorFolderRunner(self.input_dir_path, '.yml', progress_listener, self.lazy_config())


    def test_distribute_fairly_edl(self):
        distributed_edls = self.folder_processor._distribute_fairly_edl()
        comparable_distributed_elds = [list(map(lambda edl: edl.name, group)) for group in distributed_edls]

        self.assertEqual(
            [
                ['channel 1_counter-30s_2022-11-291526.mp4.yml'],
                [
                    'channel 1_counter-15s_2022-11-291526.mp4.yml',
                    'channel 1_counter-05s_2022-11-291526.mp4.yml'
                ]
            ],
            comparable_distributed_elds
        )

    def test_prepare_processing(self):
        tree = Tree("EDL to be processed")
        self.folder_processor._prepare_processing(tree)

        self.assertEqual(
            list(map(lambda f: f.name, self.input_dir_path.glob('*.pending_yml_?'))),
            [
                'channel 1_counter-05s_2022-11-291526.mp4.pending_yml_1',
                'channel 1_counter-15s_2022-11-291526.mp4.pending_yml_1',
                'channel 1_counter-30s_2022-11-291526.mp4.pending_yml_0'
            ]
        )

    def test_execute_processing(self):
        self.folder_processor.process_directory()

        self.assertEqual([], list(self.input_dir_path.iterdir()))
        self.assertEqual(3, len(list(self.output_dir_movie_path.glob('**/*.mp4'))))
        self.assertEqual(6, len(list(self.backup_dir_path.glob('**/*.*'))))

    def tearDown(self) -> None:
        shutil.rmtree(self.input_dir_path)
        shutil.rmtree(self.output_dir_path)
