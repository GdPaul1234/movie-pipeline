from pathlib import Path
from operator import itemgetter
from typing import cast
import re

from .title_serie_extractor import extract_serie_field, is_serie_from_supplied_value

forbidden_char_pattern = re.compile(r'[\/:*?<>|"]')

def naive_title(movie_path: Path, metadata, **kwargs) -> str:
    if matches := kwargs['title_pattern'].search(movie_path.stem):
        return matches.group(1)
    else:
        raise ValueError('Inappropriate file path provided: not following movie name convention')


def expanded_subtitle_title(movie_path: Path, metadata, **kwargs) -> str:
    if not metadata or '...' not in metadata['title']:
            return naive_title(movie_path, metadata, title_pattern=kwargs['base_title_pattern'])

    title, sub_title = cast(tuple[str, str], itemgetter('title', 'sub_title')(metadata))
    sub_title = sub_title.removeprefix(f'{title} : ')

    extracted_title = cast(re.Match[str], kwargs['title_pattern'].match(sub_title)).group(1)
    if is_serie_from_supplied_value(sub_title):
        episode = cast(re.Match[str], kwargs['episode_pattern'].search(sub_title)).group(1)
        extracted_title += f'__{episode}'

    return re.sub(forbidden_char_pattern, '_', extracted_title)


def subtitle_aware_title(movie_path: Path, metadata, **kwargs) -> str:
    base_title = naive_title(movie_path, metadata, **kwargs)

    if not metadata or not is_serie_from_supplied_value(metadata):
        return base_title

    episode = extract_serie_field(metadata, kwargs['episode_extractor_params'])
    season = extract_serie_field(metadata, kwargs['season_extractor_params'])
    season = '01' if season == 'xx' else season

    if episode == 'xx':
        return f"{base_title}__{metadata['sub_title'].split('.')[0]}"

    return f'{base_title} S{season}E{episode}'
