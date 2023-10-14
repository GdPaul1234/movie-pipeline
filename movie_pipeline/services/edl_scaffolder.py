import importlib
import logging
import json
import re
from pathlib import Path

import yaml
from schema import Schema

from ..lib.title_extractor.title_cleaner import TitleCleaner
from ..lib.title_extractor.title_serie_extractor import extract_title_serie_episode_from_metadata
from ..lib.title_extractor.title_extractor import ITitleExtractor
from settings import Settings

logger = logging.getLogger(__name__)


class MovieProcessedFileGenerator:
    def __init__(self, movie_file_path: Path, title_extractor: ITitleExtractor, series_extracted_metadata) -> None:
        self._movie_file_path = movie_file_path
        self._title_extractor = title_extractor
        self._series_extracted_metadata = series_extracted_metadata

    def extract_title(self) -> str:
        extracted_title = self._title_extractor.extract_title(self._movie_file_path)
        return extract_title_serie_episode_from_metadata(self._series_extracted_metadata, extracted_title)

    def generate(self):
        movie_file_suffix = self._movie_file_path.suffix
        processed_file = self._movie_file_path.with_suffix(f'{movie_file_suffix}.yml.txt')

        logger.info('Generate "%s"', processed_file)
        content = yaml.dump({'filename': f'{self.extract_title()}.mp4', 'segments': 'INSERT_SEGMENTS_HERE'})
        processed_file.write_text(content, encoding='utf-8')


channel_pattern = re.compile(r'^([^_]+)_')
title_strategies_schema = Schema({
    str: lambda strategy: strategy in ('NaiveTitleExtractor', 'SubtitleTitleExpanderExtractor', 'SerieSubTitleAwareTitleExtractor', 'SerieTitleAwareTitleExtractor')
})


class PathScaffolder:
    def __init__(self, path: Path, config: Settings) -> None:
        self._path = path
        self._config = config

        title_strategies_path = config.Paths.title_strategies
        series_extracted_metadata_path = config.Paths.series_extracted_metadata

        if title_strategies_path is not None:
            titles_strategies = yaml.safe_load(title_strategies_path.read_text('utf-8'))
            self._titles_strategies = title_strategies_schema.validate(titles_strategies)
        else:
            self._titles_strategies = {}

        if series_extracted_metadata_path is not None:
            self._series_extracted_metadata = json.loads(series_extracted_metadata_path.read_text(encoding='utf-8'))
        else:
            self._series_extracted_metadata = {}

        if (blacklist_path := config.Paths.title_re_blacklist) is not None:
            self._title_cleaner = TitleCleaner(blacklist_path)
        else:
            raise FileNotFoundError(blacklist_path)

    def _generate_file(self, file: Path) -> bool:
        if len(list(file.parent.glob(f'{file.name}.*yml'))): return False

        matches = channel_pattern.search(file.stem)

        if not matches:
            logger.warning('Skipping "%s" because its filename does not match the required pattern', file)
            return False

        channel = matches.group(1)
        title_strategy_name = self._titles_strategies.get(channel, 'NaiveTitleExtractor')
        mod = importlib.import_module('movie_pipeline.lib.title_extractor.title_extractor')
        title_strategy = getattr(mod, title_strategy_name)(self._title_cleaner)

        MovieProcessedFileGenerator(file, title_strategy, self._series_extracted_metadata).generate()
        return True

    def _scaffold_dir(self) -> bool:
        return all(self._generate_file(file) for file in self._path.glob('*.ts'))

    def scaffold(self):
        return self._scaffold_dir() if self._path.is_dir() else self._generate_file(self._path)
