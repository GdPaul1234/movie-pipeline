import xml.etree.ElementTree as ET
from pathlib import Path
from statistics import mean
from typing import Any, cast
from xml.etree.ElementTree import Element
from abc import ABC

from pydantic import BaseModel
from pydantic.types import PastDate, PositiveFloat, PositiveInt
from pydantic.utils import GetterDict

from ..models.movie_file import LegacyMovieFile

class NfoGetter(ABC, GetterDict):
    def get_xml_field_path(self, field_name: str):
        xml_field_paths = {
            'genres': 'genre',
            'directors': 'director',
            'actors': 'actor/name',
            'rating': 'ratings/rating/value'
        }

        return xml_field_paths.get(field_name) or field_name

    def get(self, key: Any, default: Any = None) -> Any:
        obj = cast(Element, self._obj)
        field_name = self.get_xml_field_path(key)

        if key in {'genres', 'directors', 'credits', 'actors'}:
            return [item.text for item in obj.findall(field_name)]

        elif key == 'rating':
            return mean(float(item.text) for item in obj.findall(field_name)) # type: ignore

        elif (item := obj.find(field_name)) is not None:
            return item.text

        return default


class BaseNfo(BaseModel, ABC):
    title: str
    rating: PositiveFloat
    plot: str
    mpaa: str
    genres: list[str]
    premiered: PastDate
    year: PositiveInt
    actors: list[str]

    class Config:
        orm_mode = True
        getter_dict = NfoGetter


class MovieNfo(BaseNfo):
    sorttitle: str
    tagline: str
    credits: list[str]
    directors: list[str]


class SerieNfo(BaseNfo):
    showtitle: str
    season: PositiveInt
    episode: PositiveInt
    aired: PastDate
    credits: list[str]
    directors: list[str]


class TvShowNfo(BaseNfo):
    pass


class NfoParser:
    @staticmethod
    def get_nfo_parser(path: Path):
        if path.name == 'tvshow.nfo':
            return TvShowNfo
        elif LegacyMovieFile(path).is_serie:
            return SerieNfo
        else:
            return MovieNfo

    @staticmethod
    def parse(path: Path):
        tree = ET.parse(path)
        parser = __class__.get_nfo_parser(path)
        return parser.from_orm(tree.getroot())
