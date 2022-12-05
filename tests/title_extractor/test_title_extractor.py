from argparse import Namespace
from pathlib import Path
import json
import unittest

from config_loader import ConfigLoader
from lib.title_extractor import NaiveTitleExtractor, SubtitleTitleExpanderExtractor

movie_metadata_path = Path(__file__).parent.joinpath('Channel 1_Movie Name_2022-12-05-2203-20.ts.metadata.json')
serie_metadata_path = Path(__file__).parent.joinpath("Channel 1_Serie Name. 'Title..._2022-12-05-2203-20.ts.metadata.json")

config_path = Path(__file__).parent.joinpath('test_config.ini')
options = Namespace()
setattr(options, 'config_path', config_path)
config = ConfigLoader(options).config


class TestTitleExtractor(unittest.TestCase):
    def test_movie_naive_title_extractor(self):
        movie_file_path = movie_metadata_path.with_name(movie_metadata_path.name.removesuffix('.metadata.json'))
        extracted_title = NaiveTitleExtractor.extract_title(movie_file_path)

        self.assertEqual('Movie Name', extracted_title)

    def test_serie_naive_title_extractor(self):
        serie_file_path = serie_metadata_path.with_name(serie_metadata_path.name.removesuffix('.metadata.json'))
        extracted_title = NaiveTitleExtractor.extract_title(serie_file_path)

        self.assertEqual("Serie Name. 'Title...", extracted_title)

    def test_movie_subtitle_title_expander_title_extractor(self):
        movie_metadata_path.write_text(json.dumps({
            "title": "Movie Name...",
            "sub_title": "Movie Name... : Movie Name, le titre long. Bla Bla Bla"
        }, indent=2))
        movie_file_path = movie_metadata_path.with_name(movie_metadata_path.name.removesuffix('.metadata.json'))
        movie_file_path.touch()

        try:
            extracted_title = SubtitleTitleExpanderExtractor.extract_title(movie_file_path)
            self.assertEqual("Movie Name, le titre long", extracted_title)
        finally:
            movie_metadata_path.unlink()
            movie_file_path.unlink()

    def test_serie_subtitle_title_expander_title_extractor(self):
        serie_metadata_path.write_text(json.dumps({
            "title": "Serie Name. \"Title...",
            "sub_title": "Serie Name. \"Title overflow!\" Série (FR)"
        }, indent=2))
        serie_file_path = serie_metadata_path.with_name(serie_metadata_path.name.removesuffix('.metadata.json'))
        serie_file_path.touch()

        try:
            extracted_title = SubtitleTitleExpanderExtractor.extract_title(serie_file_path)
            self.assertEqual("Serie Name__Title overflow!", extracted_title)
        finally:
            serie_metadata_path.unlink()
            serie_file_path.unlink()
