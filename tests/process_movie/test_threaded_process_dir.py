from argparse import Namespace
from pathlib import Path
import shutil
import textwrap
import unittest

from config_loader import ConfigLoader
from process_movie import MovieFileProcessorFolderRunner

input_dir_path = Path(__file__).parent.joinpath('in')

config_path = Path(__file__).parent.joinpath('test_config.ini')
options = Namespace()
setattr(options, 'config_path', config_path)
config = ConfigLoader(options).config

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

    def test_distribute_fairly_edl(self):
        folder_processor = MovieFileProcessorFolderRunner(input_dir_path, '.yml', config)

        distributed_edls = folder_processor._distribute_fairly_edl()
        comparable_distributed_elds = [
            list(map(lambda edl: edl.name, group))
            for group in distributed_edls
        ]

        self.assertListEqual(
            [
                ['channel 1_counter-30s_2022-11-291526.mp4.yml'],
                [
                    'channel 1_counter-15s_2022-11-291526.mp4.yml',
                    'channel 1_counter-05s_2022-11-291526.mp4.yml'
                ]
            ],
            comparable_distributed_elds
        )

    def tearDown(self) -> None:
        shutil.rmtree(input_dir_path)
