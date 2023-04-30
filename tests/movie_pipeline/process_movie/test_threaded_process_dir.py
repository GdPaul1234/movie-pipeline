import shutil
import textwrap
import unittest
from pathlib import Path

from rich.tree import Tree

from movie_pipeline.commands.process_movie import \
    MovieFileProcessorFolderRunner
from movie_pipeline.lib.ui_factory import ProgressUIFactory

from ..concerns import get_output_movies_directories, create_output_movies_directories, lazy_load_config_file

input_dir_path = Path(__file__).parent.joinpath('in')

output_dir_path, output_dir_movie_path, output_dir_serie_path, backup_dir_path = \
    get_output_movies_directories(Path(__file__).parent)

lazy_config = lazy_load_config_file(Path(__file__).parent)

class TestThreadedProcessDir(unittest.TestCase):
    def setUp(self) -> None:
        input_dir_path.mkdir()
        ressources_path = Path(__file__).parent.parent.joinpath('ressources')

        for video in ressources_path.glob('*.mp4'):
            # create video file
            video_path = input_dir_path.joinpath(f'channel 1_{video.stem}_2022-11-291526.mp4')
            shutil.copyfile(video, video_path)

            # create edl
            edl_path = video_path.with_suffix('.mp4.yml')
            edl_path.write_text(textwrap.dedent(f'''\
                filename: {video.stem}.mp4
                segments: 00:00:02.370-00:00:04.960,
            '''), encoding='utf-8')

        create_output_movies_directories(Path(__file__).parent)


    def test_distribute_fairly_edl(self):
        progress_listener = ProgressUIFactory.create_process_listener()
        folder_processor = MovieFileProcessorFolderRunner(input_dir_path, '.yml', progress_listener, lazy_config())

        distributed_edls = folder_processor._distribute_fairly_edl()
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
        progress_listener = ProgressUIFactory.create_process_listener()
        folder_processor = MovieFileProcessorFolderRunner(input_dir_path, '.yml', progress_listener, lazy_config())

        tree = Tree("EDL to be processed")
        folder_processor._prepare_processing(tree)

        self.assertEqual(
            list(map(lambda f: f.name, input_dir_path.glob('*.pending_yml_?'))),
            [
                'channel 1_counter-05s_2022-11-291526.mp4.pending_yml_1',
                'channel 1_counter-15s_2022-11-291526.mp4.pending_yml_1',
                'channel 1_counter-30s_2022-11-291526.mp4.pending_yml_0'
            ]
        )

    def test_execute_processing(self):
        progress_listener = ProgressUIFactory.create_process_listener()
        folder_processor = MovieFileProcessorFolderRunner(input_dir_path, '.yml', progress_listener, lazy_config())

        folder_processor.process_directory()

        self.assertEqual([], list(input_dir_path.iterdir()))
        self.assertEqual(3, len(list(output_dir_movie_path.glob('**/*.mp4'))))
        self.assertEqual(6, len(list(backup_dir_path.glob('**/*.*'))))

    def tearDown(self) -> None:
        shutil.rmtree(input_dir_path)
        shutil.rmtree(output_dir_path)
