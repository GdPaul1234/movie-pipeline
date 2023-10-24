from dataclasses import dataclass
import logging
import json
import re
from pathlib import Path
from typing import Any

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


channel_pattern = re.compile(r'^([^_]+)_')
title_strategies_schema = Schema({
    str: lambda strategy: strategy in ('NaiveTitleExtractor', 'SubtitleTitleExpanderExtractor', 'SerieSubTitleAwareTitleExtractor', 'SerieTitleAwareTitleExtractor')
})


@dataclass
class TitleStrategyContext:
    titles_strategies: dict[str, str]
    series_extracted_metadata: Any
    title_cleaner: TitleCleaner


def get_title_strategy_context(config: Settings) -> TitleStrategyContext:
    title_strategies_path = config.Paths.title_strategies
    series_extracted_metadata_path = config.Paths.series_extracted_metadata

    if title_strategies_path is not None:
        titles_strategies = yaml.safe_load(title_strategies_path.read_text('utf-8'))
        titles_strategies = title_strategies_schema.validate(titles_strategies)
    else:
        titles_strategies = {}

    if series_extracted_metadata_path is not None:
        series_extracted_metadata = json.loads(series_extracted_metadata_path.read_text(encoding='utf-8'))
    else:
        series_extracted_metadata = {}

    if (blacklist_path := config.Paths.title_re_blacklist) is not None:
        title_cleaner = TitleCleaner(blacklist_path)
    else:
        raise FileNotFoundError(blacklist_path)

    return TitleStrategyContext(titles_strategies, series_extracted_metadata, title_cleaner)
