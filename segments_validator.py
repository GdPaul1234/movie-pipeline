import argparse
import logging
from pathlib import Path
from typing import cast
import PySimpleGUI as sg
import os

from config_loader import ConfigLoader
from gui.segment_validators.main import main as run_gui

def main():
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname)
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

    parser.add_argument('--log-level', default='INFO', choices=levels)
    parser.add_argument('--config-path', default='config.ini', help='Config path')

    options = parser.parse_args()
    logging.basicConfig(level=options.log_level)

    config = ConfigLoader(options).config

    if fname := sg.popup_get_file('Select a video file'):
        run_gui(Path(cast(str, fname)), config)


if __name__ == '__main__':
    main()
