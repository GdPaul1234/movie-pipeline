import shutil
import unittest
from pathlib import Path

from scaffold_dir import MovieProcessedFileGenerator, scaffold_dir

input_dir_path = Path(__file__).parent.joinpath('in')
video_path = input_dir_path.joinpath('channel 1_Movie Name_2022-11-1601-20.mp4')

sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')

class TestScaffoldDir(unittest.TestCase):
    def setUp(self) -> None:
        input_dir_path.mkdir()
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

    def test_scaffold_dir(self):
        shutil.copyfile(sample_video_path, video_path.with_suffix('.ts'))

        scaffold_dir(input_dir_path)
        self.assertTrue(video_path.with_suffix('.ts.yml.txt'))

    def test_no_scaffold_dir_when_already_created(self):
        shutil.copyfile(sample_video_path, video_path.with_suffix('.ts'))
        video_path.with_suffix('.ts.yml').write_text("DON'T EDIT ME!")

        scaffold_dir(input_dir_path)

        self.assertFalse(video_path.with_suffix('.ts.yml.txt').exists())

    def test_no_scaffold_dir_when_already_processing(self):
        shutil.copyfile(sample_video_path, video_path.with_suffix('.ts'))
        video_path.with_suffix('.ts.pending_yml_2').write_text("DON'T EDIT ME!")

        scaffold_dir(input_dir_path)

        self.assertFalse(video_path.with_suffix('.ts.yml.txt').exists())

    def tearDown(self) -> None:
        shutil.rmtree(input_dir_path)
