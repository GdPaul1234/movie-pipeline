from abc import ABC
from pathlib import Path
from statistics import mean
from typing import Optional
from xml.etree.ElementTree import Element

from pydantic import computed_field
from pydantic.types import NonNegativeInt, PastDate, PositiveFloat, PositiveInt
from pydantic_xml import BaseXmlModel, RootXmlModel, element, wrapped

from ..models.movie_file import LegacyMovieFile


class Actor(RootXmlModel):
    root: str = element(tag='name')


class Rating(RootXmlModel):
    root: PositiveFloat = wrapped('rating', element(tag='value'))


class BaseNfo(BaseXmlModel, ABC, search_mode='unordered'):
    title: str = element()
    ratings: list[Rating] = element('ratings')
    plot: Optional[str] = element()
    mpaa: Optional[str] = element()
    genres:list[str] = element(tag='genre')
    premiered: PastDate = element()
    year: PositiveInt = element()
    actors: list[Actor] = element(tag='actor')

    @computed_field
    def rating(self) -> PositiveFloat:
        return mean([float(rating.root) for rating in self.ratings] or [0])


class MovieNfo(BaseNfo, tag='movie'):
    sorttitle: Optional[str] = element()
    tagline: Optional[str] = element()
    credits: list[str] = element()
    directors: list[str] = element(tag='director')


class SerieNfo(BaseNfo, tag='episodedetails'):
    showtitle: str = element()
    season: NonNegativeInt = element()
    episode: PositiveInt = element()
    aired: PastDate = element()
    credits: list[str] = element()
    directors: list[str] = element(tag='director')


class TvShowNfo(BaseNfo, tag='tvshow'):
    pass


class NfoParser():
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
        parser = __class__.get_nfo_parser(path)
        return parser.from_xml(path.read_text(encoding='utf-8'))
