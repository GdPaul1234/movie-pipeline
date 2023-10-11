from pathlib import Path
import json
import re

from .strategy import expanded_subtitle_title, naive_title, subtitle_aware_title
from .title_cleaner import TitleCleaner

title_pattern = re.compile(r"_([\w&àéèï'!., ()\[\]#-]+)_")
forbidden_char_pattern = re.compile(r'[\/:*?<>|"]')


def load_metadata(movie_path: Path):
    movie_metadata_path = movie_path.with_suffix(f'{movie_path.suffix}.metadata.json')

    if movie_metadata_path.exists():
        return json.loads(movie_metadata_path.read_text(encoding='utf-8'))


class NaiveTitleExtractor:
    def __init__(self, title_cleaner: TitleCleaner) -> None:
        self._cleaner = title_cleaner

    def extract_title(self, movie_path: Path) -> str:
        return self._cleaner.clean_title(naive_title(movie_path, None, title_pattern=title_pattern))


class SubtitleTitleExpanderExtractor:
    title_pattern = re.compile(r"([^.]+)\.")
    episode_pattern = re.compile(r". '([^']+)'")

    def __init__(self, title_cleaner: TitleCleaner) -> None:
        self._cleaner = title_cleaner

    def extract_title(self, movie_path: Path) -> str:
        metadata = load_metadata(movie_path)
        return self._cleaner.clean_title(expanded_subtitle_title(movie_path, metadata, base_title_pattern=title_pattern, title_pattern=self.title_pattern, episode_pattern=self.episode_pattern))


class SerieSubTitleAwareTitleExtractor:
    episode_extractor_params = ('sub_title', re.compile(r'(\d+)[/-]\d+'))
    season_extractor_params = ('sub_title', re.compile(r'Saison (\d+)'))

    def __init__(self, title_cleaner: TitleCleaner) -> None:
        pass

    def extract_title(self, movie_path: Path) -> str:
        metadata = load_metadata(movie_path)
        return subtitle_aware_title(movie_path, metadata, title_pattern=title_pattern, episode_extractor_params=self.episode_extractor_params, season_extractor_params=self.season_extractor_params)


class SerieTitleAwareTitleExtractor:
    episode_extractor_params = ('title', re.compile(r'(\d+)-\d+'))
    season_extractor_params = ('title', re.compile(r'Saison (\d+)'))

    def __init__(self, title_cleaner: TitleCleaner) -> None:
        pass

    def extract_title(self, movie_path: Path) -> str:
        metadata = load_metadata(movie_path)
        return subtitle_aware_title(movie_path, metadata, title_pattern=title_pattern, episode_extractor_params=self.episode_extractor_params, season_extractor_params=self.season_extractor_params)
