import argparse
import logging
from pathlib import Path
from typing import cast
import PySimpleGUI as sg
import os

from settings import Settings
from gui.segment_validators.main import main as run_gui

def main():
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname)
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

    parser.add_argument('--log-level', default='INFO', choices=levels)
    parser.add_argument('--config-path', default='config.env', help='Config path')

    options = parser.parse_args()
    logging.basicConfig(level=options.log_level)

    config = Settings(_env_file=options.config_path, _env_file_encoding='utf-8')

    if fname := sg.popup_get_file('Select a video file'):
        run_gui(Path(cast(str, fname)), config)


if __name__ == '__main__':
    main()
