from typing import Any
import PySimpleGUI as sg

status_bar = [
    sg.StatusBar('Open a file to get started', key='-FILENAME-', pad=((0,5),(0,0))),
    sg.Column([[sg.StatusBar('Vol: 100', key='-VOLUME-')]], pad=0)
]


def handle_status_bar(window: sg.Window, event: str, values: dict[str, Any]):
    pass
