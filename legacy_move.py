import logging
from pathlib import Path

from movie_file import LegacyMovieFile
from movie_path_destination_finder import MoviePathDestinationFinder

logger = logging.getLogger(__name__)

def move_movie_file_to_dest(filepath: str):
    movie_file = LegacyMovieFile(filepath)
    dest_path = MoviePathDestinationFinder(movie_file).resolve_destination()

    logger.info('Move "%s" to "%s"', movie_file.as_path(), dest_path)
    movie_file.as_path().replace(
        dest_path.joinpath(f"{movie_file.title}{movie_file.as_path().suffix}"))


def move_movie_in_directory_to_dest(folderpath: str):
    for file in Path(folderpath).iterdir():
        if file.suffix != '.mp4':
            continue
        move_movie_file_to_dest(file.resolve)


def command(options):
    logger.debug('args: %s', vars(options))
    filepath = options.file

    try:
        if Path(filepath).is_file():
            move_movie_file_to_dest(filepath)
        else:
            move_movie_in_directory_to_dest(filepath)
    except Exception as e:
        logger.exception(e)

