from pathlib import Path
from operator import itemgetter
from typing import cast
import json
import re

from ..lib.title_cleaner import TitleCleaner

title_pattern = re.compile(r"_([\w&àéèï'!., ()-]+)_")
forbidden_char_pattern = re.compile(r'[\/:*?<>|"]')

serie_hints = ['Série', 'Episode', 'Saison']
serie_hints_location = ['description', 'title', 'sub_title']
ExtractorParams = tuple[str, re.Pattern[str]]


def load_metadata(movie_path: Path):
    movie_metadata_path = movie_path.with_suffix(f'{movie_path.suffix}.metadata.json')

    if movie_metadata_path.exists():
        return json.loads(movie_metadata_path.read_text(encoding='utf-8'))


def is_serie_from_supplied_value(supplied_value: str | dict):
    def contains_any_serie_hint(value: str):
        return any([value.count(serie_hint) for serie_hint in serie_hints])

    if isinstance(supplied_value, str):
        return contains_any_serie_hint(supplied_value)

    for field in serie_hints_location:
        if contains_any_serie_hint(supplied_value[field]):
            return True

    return False


def extract_serie_field(metadata, extractor_params: ExtractorParams):
    field, pattern = extractor_params

    matches = pattern.search(metadata[field])
    return matches.group(1).rjust(2, '0') if matches else 'xx'


class NaiveTitleExtractor:
    def __init__(self, title_cleaner: TitleCleaner) -> None:
        self._cleaner = title_cleaner

    def extract_title(self, movie_path: Path) -> str:
        if matches := title_pattern.search(movie_path.stem):
            return self._cleaner.clean_title(matches.group(1))
        else:
            raise ValueError('Inappropriate file path provided: not following movie name convention')


class SubtitleTitleExpanderExtractor(NaiveTitleExtractor):
    title_pattern = re.compile(r"([^.]+)\.")
    episode_pattern = re.compile(r". '([^']+)'")

    def extract_title(self, movie_path: Path) -> str:
        metadata = load_metadata(movie_path)

        if not metadata or '...' not in metadata['title']:
            return super().extract_title(movie_path)

        title, sub_title = cast(tuple[str, str], itemgetter('title', 'sub_title')(metadata))
        sub_title = sub_title.removeprefix(f'{title} : ')

        extracted_title = cast(re.Match[str], self.title_pattern.match(sub_title)).group(1)
        if is_serie_from_supplied_value(sub_title):
            episode = cast(re.Match[str], self.episode_pattern.search(sub_title)).group(1)
            extracted_title += f'__{episode}'

        return self._cleaner.clean_title(re.sub(forbidden_char_pattern, '_', extracted_title))


class SerieSubTitleAwareTitleExtractor(NaiveTitleExtractor):
    episode_extractor_params = ('sub_title', re.compile(r'(\d+)/\d+'))
    season_extractor_params = ('sub_title', re.compile(r'Saison (\d+)'))

    def extract_title(self, movie_path: Path) -> str:
        metadata = load_metadata(movie_path)
        base_title = super().extract_title(movie_path)

        if not metadata or not is_serie_from_supplied_value(metadata):
            return base_title

        episode = extract_serie_field(metadata, self.episode_extractor_params)
        season = extract_serie_field(metadata, self.season_extractor_params)
        season = '01' if season == 'xx' else season
        return f'{base_title} S{season}E{episode}'


class SerieTitleAwareTitleExtractor(SerieSubTitleAwareTitleExtractor):
    episode_extractor_params = ('title', re.compile(r'(\d+)-\d+'))
    season_extractor_params = ('description', re.compile(r'Saison (\d+)'))
