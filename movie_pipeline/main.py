import logging
import logging.handlers
import os
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.logging import RichHandler

from .lib.util import ConsoleLoggerFilter
from .settings import Settings

app = typer.Typer()

LogLevel = StrEnum('LogLevel', ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
DetectorKey = StrEnum('DetectorKey', ['axcorrelate_silence', 'match_template', 'crop'])


config: Optional[Settings] = None


@app.command('archive_movies')
def archive_movies():
    """Archive movies regarding options in config file"""
    from movie_pipeline.commands.archive_movies import command
    if config is not None:
        command(config)


@app.command('detect_segments')
def detect_segments(
    filepath: Annotated[Path, typer.Argument(help='File or folder to process')],
    detector: Annotated[list[DetectorKey],typer.Option(help='Run detect segments with selected detectors')] = [DetectorKey.match_template]
):
    """Run best-effort segments detectors"""
    from movie_pipeline.commands.detect_segments import command
    if config is not None:
        selected_detectors_keys = [key.name for key in detector]
        command(filepath, selected_detectors_keys, config)


@app.command('process_movie')
def process_movie(
    filepath: Annotated[Path, typer.Argument(help='File or folder to process')],
    custom_ext: Annotated[str, typer.Option(help='Extension of Processing decision files')] = '.yml',
    web: Annotated[bool, typer.Option(help='Use the new folder movie file processor and launch the web dashboard')] = False
):
    """Cut and merge movie segments to keep only relevant part"""
    from movie_pipeline.commands.process_movie import command
    if config is not None:
        command(filepath, custom_ext, config, web)


def version_callback(value: bool):
    if value:
        from importlib.metadata import version
        print(f"movie_pipeline Version: {version('movie_pipeline')}")
        raise typer.Exit()


@app.callback()
def main(
    log_level: Annotated[LogLevel, typer.Option()] = LogLevel.INFO,
    config_path: Annotated[Path, typer.Option(readable=True, help='Config path')] = Path.home() / '.movie_pipeline' / 'config.env',
    version: Annotated[Optional[bool], typer.Option('--version', callback=version_callback)] = None
):
    """Available commands:"""
    global config

    if not config_path.is_file():
        config_path.write_text('')

    os.chdir(config_path.parent)
    config = Settings(_env_file=config_path,  _env_file_encoding='utf-8')  # type: ignore

    # Could get fancy here and load configuration from file or dictionary
    fh = logging.handlers.TimedRotatingFileHandler(filename=config.Logger.file_path if config.Logger else 'log.txt')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    ch = RichHandler(rich_tracebacks=True)
    ch.setFormatter(logging.Formatter('%(message)s'))
    ch.addFilter(ConsoleLoggerFilter())

    logging.basicConfig(level=log_level.name, handlers=(fh, ch,))
