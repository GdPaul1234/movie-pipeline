import re

ExtractorParams = tuple[str, re.Pattern[str]]
serie_hints = ['Série', 'Saison']
serie_hints_location = ['description', 'title', 'sub_title']


def extract_serie_field(metadata, extractor_params: ExtractorParams):
    field, pattern = extractor_params

    matches = pattern.search(metadata[field])
    return matches.group(1).rjust(2, '0') if matches else 'xx'


def is_serie_from_supplied_value(supplied_value: str | dict):
    def contains_any_serie_hint(value: str):
        return any(value.count(serie_hint) for serie_hint in serie_hints)

    if isinstance(supplied_value, str):
        return contains_any_serie_hint(supplied_value)
    return any(contains_any_serie_hint(supplied_value[field]) for field in serie_hints_location)


def extract_title_serie_episode_from_metadata(series_extracted_metadata: dict[str, dict[str, dict[str, str]]], extracted_title: str):
    if re.search(r'S\d{2}E\d{2,3}', extracted_title) is not None:
        return extracted_title

    m = re.match(r'(?P<showtitle>^[^_]+)__(?P<title>.+)', extracted_title) \
        or re.match(r"(?P<showtitle>[\w&àéèï'!., ()\[\]#-]+) '(?P<title>.+)'", extracted_title)

    if m is not None:
        formatted_episode = series_extracted_metadata.get(m.group('showtitle'), {}).get(m.group('title'), {}).get('formattedEpisode')
        return f"{m.group('showtitle')} {formatted_episode}"
    else:
        return extracted_title
