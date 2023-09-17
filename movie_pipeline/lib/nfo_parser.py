from abc import ABC
from pathlib import Path
from statistics import mean
from typing import Optional

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
    plot: Optional[str] = element(default=None)
    mpaa: Optional[str] = element(default=None)
    genres:list[str] = element(tag='genre')
    premiered: PastDate = element()
    year: PositiveInt = element()
    actors: list[Actor] = element(tag='actor', default=[])

    @computed_field
    def rating(self) -> PositiveFloat:
        return mean([float(rating.root) for rating in self.ratings] or [0])


class MovieNfo(BaseNfo, tag='movie'):
    sorttitle: Optional[str] = element(default=None)
    tagline: Optional[str] = element(default=None)
    credits: list[str] = element(default=[])
    directors: list[str] = element(tag='director', default=[])


class SerieNfo(BaseNfo, tag='episodedetails'):
    showtitle: str = element()
    season: NonNegativeInt = element()
    episode: PositiveInt = element()
    aired: Optional[PastDate] = element(default=None)
    credits: list[str] = element(default=[])
    directors: list[str] = element(tag='director', default=[])


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
