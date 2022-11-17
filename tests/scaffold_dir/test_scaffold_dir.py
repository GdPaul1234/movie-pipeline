import shutil
import unittest
from pathlib import Path

from scaffold_dir import MovieProcessedFileGenerator

input_dir_path = Path(__file__).parent.joinpath('in')
video_path = input_dir_path.joinpath('channel 1_Movie Name_2022-11-1601-20.mp4')

class TestScaffoldDir(unittest.TestCase):
    def setUp(self) -> None:
        input_dir_path.mkdir()
        sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')
        shutil.copyfile(sample_video_path, video_path)

    def test_extract_title(self):
        edl_template = MovieProcessedFileGenerator(video_path)
        self.assertEqual('Movie Name', edl_template.extract_title())

    def test_generate_edl_file(self):
        edl_template = MovieProcessedFileGenerator(video_path)

        edl_template.generate()

        expected_content = 'filename: Movie Name.mp4\nsegments: INSERT_SEGMENTS_HERE\n'
        actual_content = video_path.with_suffix('.mp4.yml.txt').read_text()
        self.assertEqual(expected_content, actual_content)

    def tearDown(self) -> None:
        shutil.rmtree(input_dir_path)
