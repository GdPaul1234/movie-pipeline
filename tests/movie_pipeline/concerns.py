from pathlib import Path
from typing import Callable, NotRequired, TypedDict
from settings import Settings
import shutil

def get_output_movies_directories(base_path_folder: Path):
    output_dir_path = base_path_folder / 'out'

    movie_dir_path = output_dir_path / 'Films'
    serie_dir_path = output_dir_path / 'Séries'
    backup_dir_path = output_dir_path / 'backup'

    return output_dir_path, movie_dir_path, serie_dir_path, backup_dir_path


def lazy_load_config_file(base_path_folder: Path):
    config_path = base_path_folder / 'test_config.env'

    return lambda: Settings(_env_file=config_path, _env_file_encoding='utf-8') # type: ignore


def create_output_movies_directories(base_path_folder: Path):
    make_dirs(list(get_output_movies_directories(base_path_folder)))


class SourceDestinationDict(TypedDict):
    source: Path
    destination: Path
    after_copy: NotRequired[Callable[[Path], None]]


def make_dirs(paths: list[Path]):
    for path in paths:
        path.mkdir(parents=True)


def copy_files(rules: list[SourceDestinationDict]):
    for rule in rules:
        rule['destination'].parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(rule['source'], rule['destination'])

        if (after_copy_fn := rule.get('after_copy')) is not None:
            after_copy_fn(rule['destination'])
