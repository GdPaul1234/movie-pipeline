import re
from pathlib import Path

from ..models.movie_file import LegacyMovieFile


class MoviePathDestinationFinder:
    def __init__(self, movie_file: LegacyMovieFile, config) -> None:
        self._movie_file = movie_file
        self._paths = config['Paths']

    def _find_or_create_serie_folder(self, series_path: Path, serie_file: LegacyMovieFile) -> Path:
        serie_file_name = re.sub(r' S\d{2}E\d{2,}$', '', serie_file.title)
        season_number = int(re.search(r'S(\d{2})E\d{2,}$', serie_file.title).group(1))
        season_folder_name = f'Saison {season_number}'

        matches_series = [p for p in series_path.iterdir()
                          if p.is_dir() and p.name.lower().startswith(serie_file_name.lower())]
        if not len(matches_series):
            created_serie_folder = series_path.joinpath(serie_file_name, season_folder_name)
            created_serie_folder.mkdir(parents=True)
            return created_serie_folder
        else:
            serie_folder = matches_series[0]
            season_folder = serie_folder.joinpath(season_folder_name)
            if not season_folder.is_dir():
                season_folder.mkdir()
            return season_folder

    def resolve_destination(self):
        if self._movie_file.is_serie:
            series_folder_path = Path(self._paths.get('series_folder'))
            return self._find_or_create_serie_folder(series_folder_path, self._movie_file)
        else:
            movies_folder_path = Path(self._paths.get('movies_folder'))
            dest_path = movies_folder_path.joinpath(self._movie_file.title)
            dest_path.mkdir()
            return dest_path
