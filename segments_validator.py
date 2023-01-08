from pathlib import Path
import PySimpleGUI as sg

from gui.segment_validators.main import main

if __name__ == '__main__':
    if fname := sg.popup_get_file('Select a video file'):
        main(Path(fname))
