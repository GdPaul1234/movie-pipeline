from pathlib import Path
from operator import itemgetter
from typing import cast
import json
import re

title_pattern = re.compile(r"_([\w&àéèï'!., ()-]+)_")
forbidden_char_pattern = re.compile(r'[\/:*?<>|"]')

def load_metadata(movie_file_path: Path):
    movie_metadata_file_path = movie_file_path.with_suffix(f'{movie_file_path.suffix}.metadata.json')

    if movie_metadata_file_path.exists():
        return json.loads(movie_metadata_file_path.read_text(encoding='utf-8'))


class NaiveTitleExtractor:
    @staticmethod
    def extract_title(movie_file_path: Path) -> str:
        matches = title_pattern.search(movie_file_path.stem)
        return cast(re.Match[str], matches).group(1)


class SubtitleTitleExpanderExtractor:
    title_pattern = re.compile(r"([^.]+)\.")
    episode_pattern = re.compile(r'. "([^"]+)"')

    @staticmethod
    def extract_title(movie_file_path: Path) -> str:
        metadata = load_metadata(movie_file_path)

        if not metadata:
            return NaiveTitleExtractor.extract_title(movie_file_path)

        title, sub_title = cast(tuple[str, str], itemgetter('title', 'sub_title')(metadata))
        sub_title = sub_title.removeprefix(f'{title} : ')

        extracted_title = cast(re.Match[str], __class__.title_pattern.match(sub_title)).group(1)
        if 'Série' in sub_title:
            episode = cast(re.Match[str], __class__.episode_pattern.search(sub_title)).group(1)
            extracted_title += f'__{episode}'

        return re.sub(forbidden_char_pattern, '_', extracted_title)
