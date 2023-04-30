from functools import lru_cache
from pathlib import Path
from typing import Literal, cast
import logging
import sqlite3

from deffcode import Sourcer
from settings import Settings

from ..lib.nfo_parser import BaseNfo, MovieNfo, NfoParser, SerieNfo, TvShowNfo

logger = logging.getLogger(__name__)


class MediaDatabaseUpdater:
    def __init__(self, db_path: Path) -> None:
        self._connection = sqlite3.connect(db_path)
        self._inserted_series: dict[str, int] = {}
        self.inserted_medias: set[Path] = set()
        self.init_database()

    def close(self):
        self._connection.close()

    def init_database(self):
        with self._connection as con:
            migration_path = Path(__file__).parent.parent.joinpath('lib', 'migrations', '001_medias_init.sql')
            for statement in migration_path.read_text(encoding="utf-8").split(";"):
                con.execute(statement)

    def _insert_common_subfields(self, nfo: BaseNfo, media_type: Literal['movie', 'serie', 'episode'], media_id: int):
        if media_type not in ('movie', 'serie', 'episode'):
            raise ValueError(f'Unknown {media_type=}')

        @lru_cache
        def insert_genre(genre: str) -> int:
            with self._connection as con:
                cur = con.execute(
                    "INSERT OR IGNORE INTO genres(genre) VALUES(:genre) RETURNING id",
                    {"genre": genre}
                )
                genre_id, = cur.fetchone()
            return genre_id

        @lru_cache
        def insert_person(full_name: str) -> int:
            with self._connection as con:
                cur = con.execute(
                    "INSERT OR IGNORE INTO people(name) VALUES(:name) RETURNING id",
                    {"name": full_name}
                )
                person_id, = cur.fetchone()
            return person_id

        genres_id = [insert_genre(genre) for genre in nfo.genres]
        actors_relations = [(insert_person(actor), 'actor') for actor in nfo.actors]
        credits_relations = [(insert_person(credit), 'credit') for credit in getattr(nfo, 'credits', [])]
        directors_relations = [(insert_person(director), 'director') for director in getattr(nfo, 'directors', [])]

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'{insert_genre.cache_info()=}')
            logger.debug(f'{insert_person.cache_info()=}')

        with self._connection as con:
            con.executemany(
                "INSERT OR IGNORE INTO mediable_genres(media_type,media_id,genre_id) VALUES(:media_type,:media_id,:genre_id)",
                [{'media_type': media_type, 'media_id': media_id, 'genre_id': genre_id} for genre_id in genres_id]
            )

            con.executemany(
                "INSERT OR IGNORE INTO people_mediable_relation(person_id,media_type,media_id,relation) VALUES(:person_id,:media_type,:media_id,:relation)",
                [
                    {'person_id': relation_id, 'media_type': media_type, 'media_id': media_id, 'relation': relation_type}
                    for relation_id, relation_type in (actors_relations + credits_relations + directors_relations)
                ]
            )

    def _insert_movie(self, nfo: MovieNfo) -> int:
        with self._connection as con:
            cur = con.execute(
                "INSERT OR IGNORE INTO movies(title,year,rating,mpaa) VALUES(:title,:year,:rating,:mpaa) RETURNING id",
                nfo.dict(include={'title', 'year', 'rating', 'mpaa'})
            )
            movie_id, = cur.fetchone()
            self._insert_common_subfields(nfo, media_id=movie_id, media_type='movie')
        return movie_id

    def _insert_serie(self, nfo: SerieNfo) -> int:
        with self._connection as con:
            cur = con.execute(
                "INSERT OR IGNORE INTO episodes(serie_id,title,season,episode,year,rating,mpaa) VALUES(:serie_id,:title,:season,:episode,:year,:rating,:mpaa) RETURNING id",
                {'serie_id': self._inserted_series[nfo.showtitle]} | nfo.dict(include={'title', 'season', 'episode', 'year', 'rating', 'mpaa'})
            )
            serie_id, = cur.fetchone()
            self._insert_common_subfields(nfo, media_id=serie_id, media_type='episode')
        return serie_id

    def _insert_tvshow(self, nfo: TvShowNfo) -> int:
        with self._connection as con:
            cur = con.execute(
                "INSERT OR IGNORE INTO series(title,year,rating,mpaa) VALUES(:title,:year,:rating,:mpaa) RETURNING id",
                nfo.dict(include={'title', 'year', 'rating', 'mpaa'})
            )
            tvshow_id, = cur.fetchone()
            self._insert_common_subfields(nfo, media_id=tvshow_id, media_type='serie')
        return tvshow_id

    def insert_media(self, nfo_path: Path, nfo: BaseNfo):
        if isinstance(nfo, TvShowNfo):
            self._inserted_series[nfo.title] = self._insert_tvshow(nfo)
        else:
            if isinstance(nfo, SerieNfo):
                nfo_id = self._insert_serie(nfo)
            else:
                nfo_id = self._insert_movie(nfo) # type: ignore

            media_path = nfo_path.with_suffix('.mp4')
            metadata = cast(dict, Sourcer(str(media_path)).probe_stream().retrieve_metadata())

            with self._connection as con:
                cur = con.execute(
                    "INSERT OR IGNORE INTO medias(filepath,duration,created_at,media_type,media_id) VALUES(:filepath,:duration,:created_at,:media_type,:media_id) RETURNING id",
                    {
                        'filepath': str(media_path),
                        'duration': metadata['source_duration_sec'],
                        'created_at': int(media_path.stat().st_ctime),
                        'media_type': 'episode' if isinstance(nfo, SerieNfo) else 'movie',
                        'media_id': nfo_id
                    }
                )
                media_id, = cur.fetchone()
                logger.debug(f'Insert {media_path=} ({media_id=})')
                self.inserted_medias.add(media_path)


class MediaScanner:
    pass


def command(options, config: Settings):
    logger.debug('args: %s', vars(options))

    if config.MediaDatabase is None:
        raise ValueError('Missing MediaDatabase configuration in config')

    filepath = Path(options.file)
    db_path = config.MediaDatabase.db_path

    try:
        if filepath.is_file() and filepath.suffix == '.nfo':
            MediaDatabaseUpdater(db_path).insert_media(nfo_path=filepath, nfo=NfoParser.parse(filepath))
        elif filepath.is_dir():
            pass # TODO implement media scanner
        else:
            raise ValueError('Unknown file type')
    except Exception as e:
        logger.exception(e)

