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
