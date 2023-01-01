import logging
from pathlib import Path

from models.movie_file import LegacyMovieFile
from lib.movie_path_destination_finder import MoviePathDestinationFinder

logger = logging.getLogger(__name__)


def move_movie_file_to_dest(filepath: Path | str, config):
    movie_file = LegacyMovieFile(filepath)
    dest_path = MoviePathDestinationFinder(movie_file, config).resolve_destination()

    logger.info('Move "%s" to "%s"', movie_file.as_path(), dest_path)
    movie_file.as_path().replace(dest_path.joinpath(f"{movie_file.title}{movie_file.as_path().suffix}"))


def move_movie_in_directory_to_dest(folderpath: str, config):
    for file in Path(folderpath).glob('*.mp4'):
        move_movie_file_to_dest(file.resolve(), config)


def command(options, config):
    logger.debug('args: %s', vars(options))
    filepath = options.file

    try:
        if Path(filepath).is_file():
            move_movie_file_to_dest(filepath, config)
        else:
            move_movie_in_directory_to_dest(filepath, config)
    except Exception as e:
        logger.exception(e)
