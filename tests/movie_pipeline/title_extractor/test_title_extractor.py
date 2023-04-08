from contextlib import contextmanager
from pathlib import Path
import json
import unittest

from movie_pipeline.lib.title_cleaner import TitleCleaner
from movie_pipeline.lib.title_extractor import (
    NaiveTitleExtractor,
    SerieSubTitleAwareTitleExtractor,
    SerieTitleAwareTitleExtractor,
    SubtitleTitleExpanderExtractor
)

movie_metadata_path = Path(__file__).parent.joinpath('Channel 1_Movie Name_2022-12-05-2203-20.ts.metadata.json')
serie_metadata_path = Path(__file__).parent.joinpath("Channel 1_Serie Name. 'Title..._2022-12-05-2203-20.ts.metadata.json")

blacklist_path = Path(__file__).parent.parent.joinpath('ressources', 'test_title_re_blacklist.txt')
default_title_cleaner = TitleCleaner(blacklist_path)


@contextmanager
def file_path_with_metadata_content(content: str, metadata_path: Path):
    metadata_path.write_text(content)
    file_path = metadata_path.with_name(metadata_path.name.removesuffix('.metadata.json'))
    file_path.touch()

    try:
        yield file_path
    finally:
        metadata_path.unlink()
        file_path.unlink()


class TestTitleExtractor(unittest.TestCase):
    def test_movie_naive_title_extractor(self):
        movie_file_path = movie_metadata_path.with_name(movie_metadata_path.name.removesuffix('.metadata.json'))
        title_extractor = NaiveTitleExtractor(default_title_cleaner)
        extracted_title = title_extractor.extract_title(movie_file_path)

        self.assertEqual('Movie Name', extracted_title)

    def test_serie_naive_title_extractor(self):
        serie_file_path = serie_metadata_path.with_name(serie_metadata_path.name.removesuffix('.metadata.json'))
        title_extractor = NaiveTitleExtractor(default_title_cleaner)
        extracted_title = title_extractor.extract_title(serie_file_path)

        self.assertEqual("Serie Name. 'Title...", extracted_title)

    def test_movie_subtitle_title_expander_title_extractor(self):
        content = json.dumps({
            "title": "Movie Name...",
            "sub_title": "Movie Name... : Movie Name, le titre long. Bla Bla Bla"
        }, indent=2)

        with file_path_with_metadata_content(content, movie_metadata_path) as movie_file_path:
            title_extractor = SubtitleTitleExpanderExtractor(default_title_cleaner)
            extracted_title = title_extractor.extract_title(movie_file_path)
            self.assertEqual("Movie Name, le titre long", extracted_title)

    def test_serie_subtitle_title_expander_title_extractor(self):
        content = json.dumps({
            "title": "Serie Name. \"Title...",
            "sub_title": "Serie Name. 'Title overflow!' Série (FR)"
        }, indent=2)

        with file_path_with_metadata_content(content, serie_metadata_path) as serie_file_path:
            title_extractor = SubtitleTitleExpanderExtractor(default_title_cleaner)
            extracted_title = title_extractor.extract_title(serie_file_path)
            self.assertEqual("Serie Name__Title overflow!", extracted_title)

    def test_serie_subtitle_aware_title_extractor(self):
        test_serie_metadata_path = serie_metadata_path.with_name('Channel 1_Serie Name_2022-12-05-2203-20.ts.metadata.json')
        content = json.dumps({
            "title": "Serie Name",
            "sub_title": "Serie Name : Episode Name. Série policière. 2022. Saison 1. 16/26.",
            "description": ""
        }, indent=2)

        with file_path_with_metadata_content(content, test_serie_metadata_path) as serie_file_path:
            title_extractor = SerieSubTitleAwareTitleExtractor(default_title_cleaner)
            extracted_title = title_extractor.extract_title(serie_file_path)
            self.assertEqual("Serie Name S01E16", extracted_title)

    def test_serie_title_aware_title_extractor(self):
        test_serie_metadata_path = serie_metadata_path.with_name('Channel 1_Serie Name_2022-12-05-2203-20.ts.metadata.json')
        content = json.dumps({
            "title": "Serie Name (2-3)",
            "sub_title": "",
            "description": "Série documentaire (France, 2022, 52 min) Description",
        }, indent=2)

        with file_path_with_metadata_content(content, test_serie_metadata_path) as serie_file_path:
            title_extractor = SerieTitleAwareTitleExtractor(default_title_cleaner)
            extracted_title = title_extractor.extract_title(serie_file_path)
            self.assertEqual("Serie Name S01E02", extracted_title)
