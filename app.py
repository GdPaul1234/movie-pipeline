# https://docs.python.org/3/howto/logging-cookbook.html#a-cli-application-starter-template

import argparse
import importlib
import logging
import logging.handlers
from rich.logging import RichHandler
from pathlib import Path
import os
import sys

from settings import Settings
from util import ConsoleLoggerFilter

def main():
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname)
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

    parser.add_argument('--log-level', default='INFO', choices=levels)
    parser.add_argument('--config-path', default='config.env', help='Config path', type=Path)
    subparsers = parser.add_subparsers(dest='command', help='Available commands:')

    # process command
    process_cmd = subparsers.add_parser('process_movie', help='Cut and merge movie segments to keep only relevant parts')
    process_cmd.add_argument('file', metavar='FILE', help='File or folder to process', type=Path)
    process_cmd.add_argument('--custom-ext', help='Extension of processing decision file', default='.yml')
    process_cmd.add_argument('--web', help='Use the new folder movie file processor and launch the web dashboard', action='store_true')

    # archive movies command
    subparsers.add_parser('archive_movies', help='Archive movies regarding options in config file')

    # detect segments
    detect_segments_cmd = subparsers.add_parser('detect_segments', help='Run best-effort segments detectors')
    detect_segments_cmd.add_argument('file', metavar='FILE', help='Movie to be processed', type=Path)
    detect_segments_cmd.add_argument('--detector',
                                     choices=('axcorrelate_silence', 'match_template', 'crop'),
                                     help='Run detect segments with selected detectors', nargs='+', default=['match_template'])

    # validate dir
    validate_dir_cmd = subparsers.add_parser('validate_dir', help='Validate segments and generate edit decision files in given directory')
    validate_dir_cmd.add_argument('dir', metavar='DIR', help='Directory of movies to be processed', type=Path)

    options = parser.parse_args()
    # the code to dispatch commands could all be in this file. For the purposes
    # of illustration only, we implement each command in a separate module.
    try:
        mod = importlib.import_module(f'movie_pipeline.commands.{options.command}')
        cmd = getattr(mod, 'command')
    except (ImportError, AttributeError):
        print('Unable to find the code for command \'%s\'' % options.command)
        return 1

    config = Settings(_env_file=options.config_path, _env_file_encoding='utf-8') # type: ignore

    # Could get fancy here and load configuration from file or dictionary
    fh = logging.handlers.TimedRotatingFileHandler( filename=config.Logger.file_path if config.Logger else 'log.txt')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    ch = RichHandler(rich_tracebacks=True)
    ch.setFormatter(logging.Formatter('%(message)s'))
    ch.addFilter(ConsoleLoggerFilter())

    logging.basicConfig(level=options.log_level, handlers=(fh, ch,))

    cmd(options, config)


if __name__ == '__main__':
    sys.exit(main())
