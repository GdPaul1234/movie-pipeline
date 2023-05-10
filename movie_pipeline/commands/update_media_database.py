from functools import lru_cache
from pathlib import Path
from typing import Literal, cast
import logging
import sqlite3

from deffcode import Sourcer
from rich.progress import Progress

from settings import Settings

from ..lib.nfo_parser import BaseNfo, MovieNfo, NfoParser, SerieNfo, TvShowNfo

logger = logging.getLogger(__name__)


class MediaDatabaseUpdater:
    def __init__(self, db_path: Path) -> None:
        self._connection = sqlite3.connect(db_path)
        self.common_subfields_builder = MediaDatabaseUpdater.CommonSubfieldsBuilder(self._connection)
        self._inserted_series: dict[str, int] = {}
        self.inserted_medias: set[Path] = set()
        self.init_database()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def close(self):
        self._connection.close()

    #region CommonSubfieldsBuilder
    class CommonSubfieldsBuilder:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self._connection = connection

        @lru_cache
        def _insert_genre(self, genre: str) -> int:
            with self._connection as con:
                cur = con.execute(
                    "INSERT INTO genres(genre) VALUES(:genre) ON CONFLICT DO UPDATE SET id=id RETURNING id",
                    {"genre": genre}
                )
                genre_id, = cur.fetchone()
            return genre_id

        @lru_cache
        def _insert_person(self, full_name: str) -> int:
            with self._connection as con:
                cur = con.execute(
                    "INSERT INTO people(name) VALUES(:name) ON CONFLICT DO UPDATE SET id=id RETURNING id",
                    {"name": full_name}
                )
                person_id, = cur.fetchone()
            return person_id

        def insert_common_subfields(self, nfo: BaseNfo, media_type: Literal['movie', 'serie', 'episode'], media_id: int):
            if media_type not in ('movie', 'serie', 'episode'):
                raise ValueError(f'Unknown {media_type=}')

            genres_id = [self._insert_genre(genre) for genre in nfo.genres]
            actors_relations = [(self._insert_person(actor), 'actor') for actor in nfo.actors]
            credits_relations = [(self._insert_person(credit), 'credit') for credit in getattr(nfo, 'credits', [])]
            directors_relations = [(self._insert_person(director), 'director') for director in getattr(nfo, 'directors', [])]

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'{self._insert_genre.cache_info()=}')
                logger.debug(f'{self._insert_person.cache_info()=}')

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
    #endregion CommonSubfieldsBuilder

    def init_database(self):
        with self._connection as con:
            migration_path = Path(__file__).parent.parent.joinpath('lib', 'migrations', '001_medias_init.sql')
            for statement in migration_path.read_text(encoding="utf-8").split(";"):
                con.execute(statement)

    @property
    def already_inserted_nfos(self):
        with self._connection as con:
            cur = con.execute("SELECT filepath from medias")
            filepaths = cur.fetchall()

        return {Path(filepath).with_suffix('.nfo') for filepath, in filepaths}

    def clean_media_database(self):
        with self._connection as con:
            cur = con.execute("SELECT filepath, id from medias")
            filepaths = cur.fetchall()

            missing_media_ids = [id for filepath, id in filepaths if not Path(filepath).is_file()]
            cur = con.execute(f"DELETE FROM medias WHERE id IN ({', '.join('?' * len(missing_media_ids))})", missing_media_ids)
            logger.info(f'Delete {cur.rowcount} missing medias')


    def _insert_common_subfields(self, nfo: BaseNfo, media_type: Literal['movie', 'serie', 'episode'], media_id: int):
        self.common_subfields_builder.insert_common_subfields(nfo, media_type, media_id)

    def _insert_movie(self, nfo: MovieNfo) -> int:
        with self._connection as con:
            cur = con.execute(
                "INSERT INTO movies(title,year,rating,mpaa) VALUES(:title,:year,:rating,:mpaa) ON CONFLICT DO UPDATE SET id=id RETURNING id",
                nfo.dict(include={'title', 'year', 'rating', 'mpaa'})
            )
            movie_id, = cur.fetchone()
            self._insert_common_subfields(nfo, media_id=movie_id, media_type='movie')
        return movie_id

    def _insert_serie(self, nfo_path: Path, nfo: SerieNfo) -> int:
        if (not (tvshow_nfo_path := nfo_path.parent.parent.joinpath('tvshow.nfo')).is_file()):
            raise ValueError(f'Missing tvshow.nfo (checking "{str(tvshow_nfo_path)}")')
        tvshow_id = self._inserted_series.get(nfo.showtitle) or self._insert_tvshow(cast(TvShowNfo, NfoParser.parse(tvshow_nfo_path)))

        with self._connection as con:
            cur = con.execute(
                "INSERT INTO episodes(serie_id,title,season,episode,year,rating,mpaa) VALUES(:serie_id,:title,:season,:episode,:year,:rating,:mpaa) ON CONFLICT DO UPDATE SET id=id RETURNING id",
                {'serie_id': tvshow_id} | nfo.dict(include={'title', 'season', 'episode', 'year', 'rating', 'mpaa'})
            )
            serie_id, = cur.fetchone()
            self._insert_common_subfields(nfo, media_id=serie_id, media_type='episode')
        return serie_id

    def _insert_tvshow(self, nfo: TvShowNfo) -> int:
        with self._connection as con:
            cur = con.execute(
                "INSERT INTO series(title,year,rating,mpaa) VALUES(:title,:year,:rating,:mpaa) ON CONFLICT DO UPDATE SET id=id RETURNING id",
                nfo.dict(include={'title', 'year', 'rating', 'mpaa'})
            )
            tvshow_id, = cur.fetchone()
            self._insert_common_subfields(nfo, media_id=tvshow_id, media_type='serie')
            self._inserted_series[nfo.title] = tvshow_id
        return tvshow_id

    def insert_media(self, nfo_path: Path):
        nfo = NfoParser.parse(nfo_path)

        if isinstance(nfo, TvShowNfo):
            self._inserted_series[nfo.title] = self._insert_tvshow(nfo)
        else:
            if isinstance(nfo, SerieNfo):
                nfo_id = self._insert_serie(nfo_path, nfo)
            else:
                nfo_id = self._insert_movie(nfo) # type: ignore

            media_path = nfo_path.with_suffix('.mp4')
            metadata = cast(dict, Sourcer(str(media_path)).probe_stream().retrieve_metadata())

            with self._connection as con:
                cur = con.execute(
                    "INSERT INTO medias(filepath,duration,created_at,media_type,media_id) VALUES(:filepath,:duration,:created_at,:media_type,:media_id) ON CONFLICT DO UPDATE SET id=id RETURNING id",
                    {
                        'filepath': str(media_path),
                        'duration': metadata['source_duration_sec'],
                        'created_at': int(media_path.stat().st_ctime),
                        'media_type': 'episode' if isinstance(nfo, SerieNfo) else 'movie',
                        'media_id': nfo_id
                    }
                )
                media_id, = cur.fetchone()
                logger.debug(f'Insert "{media_path=}" ({media_id=})')
                self.inserted_medias.add(media_path)


class MediaScanner:
    def __init__(self, dir_path: Path, db_path: Path, config: Settings) -> None:
        self._media_db_updater = MediaDatabaseUpdater(db_path)
        self._dir_path = dir_path
        self._config = config

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._media_db_updater.close()
        return False

    def scan(self):
        logger.info(f'Scanning "{self._dir_path}"...')
        nfos = set(self._dir_path.glob('**/*.nfo'))
        nfo_to_scan = nfos - self._media_db_updater.already_inserted_nfos
        logger.info(f'Found {len(nfos)} NFOs, {len(nfo_to_scan)} to scan')

        nfo_errors = []

        with Progress() as progress:
            for nfo_path in progress.track(nfo_to_scan):
                try:
                    message = f'Inserting "{str(nfo_path)}"...'
                    logger.info(message); progress.console.log(message)
                    self._media_db_updater.insert_media(nfo_path)
                except Exception as e:
                    logger.exception(e)
                    nfo_errors.append(nfo_path)

        if self._config.MediaDatabase.clean_after_update: # type: ignore
            logger.info('Cleaning database...')
            self._media_db_updater.clean_media_database()

        if len(nfo_errors) > 0:
            logger.warning(f"Errors found in:\n{list(map(str, nfo_errors))}")


def command(options, config: Settings):
    logger.debug('args: %s', vars(options))

    if config.MediaDatabase is None:
        raise ValueError('Missing MediaDatabase configuration in config')

    filepath = Path(options.file)
    db_path = config.MediaDatabase.db_path

    try:
        if filepath.is_file() and filepath.suffix == '.nfo':
            with MediaDatabaseUpdater(db_path) as updater:
                updater.insert_media(nfo_path=filepath)
        elif filepath.is_dir():
            with MediaScanner(filepath, db_path, config) as scanner:
                scanner.scan()
        else:
            raise ValueError('Unknown file type')
    except Exception as e:
        logger.exception(e)

