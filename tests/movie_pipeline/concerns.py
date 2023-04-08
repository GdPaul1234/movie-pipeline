from pathlib import Path
from settings import Settings

def get_output_movies_directories(base_path_folder: Path):
    output_dir_path = base_path_folder / 'out'

    movie_dir_path = output_dir_path / 'Films'
    serie_dir_path = output_dir_path / 'Séries'
    backup_dir_path = output_dir_path / 'backup'

    return output_dir_path, movie_dir_path, serie_dir_path, backup_dir_path


def lazy_load_config_file(base_path_folder: Path):
    config_path = base_path_folder / 'test_config.env'

    return lambda: Settings(_env_file=config_path, _env_file_encoding='utf-8') # type: ignore

