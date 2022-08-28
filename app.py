# https://docs.python.org/3/howto/logging-cookbook.html#a-cli-application-starter-template

import argparse
import importlib
import logging
import logging.handlers
import os
import sys

from config_loader import ConfigLoader

config = ConfigLoader().config


def main():
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname)
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

    parser.add_argument('--log-level', default='INFO', choices=levels)
    subparsers = parser.add_subparsers(
        dest='command', help='Available commands:')

    # move command
    move_cmd = subparsers.add_parser(
        'legacy_move', help='Move converted movies or series to their folder')
    move_cmd.add_argument('file', metavar='FILE',
                          help='File or folder to move')

    # process command
    process_cmd = subparsers.add_parser(
        'process_movie', help='Cut and merge movies to keep only relevant parts')
    process_cmd.add_argument('file', metavar='FILE',
                             help='File or folder to process')

    options = parser.parse_args()
    # the code to dispatch commands could all be in this file. For the purposes
    # of illustration only, we implement each command in a separate module.
    try:
        mod = importlib.import_module(options.command)
        cmd = getattr(mod, 'command')
    except (ImportError, AttributeError):
        print('Unable to find the code for command \'%s\'' % options.command)
        return 1

    # Could get fancy here and load configuration from file or dictionary
    fh = logging.handlers.TimedRotatingFileHandler(
        filename=config.get('Logger', 'file_path', fallback='log.txt'))

    ch = logging.StreamHandler()

    logging.basicConfig(
        level=options.log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=(fh, ch,))

    cmd(options)


if __name__ == '__main__':
    sys.exit(main())
