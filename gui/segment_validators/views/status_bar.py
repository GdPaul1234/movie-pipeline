from typing import Any
import PySimpleGUI as sg

from util import seconds_to_position

status_bar = [
    sg.StatusBar('Open a file to get started', key='-FILENAME-', pad=((0,5),(0,0))),
    sg.Column([[sg.StatusBar('Dur: 00:00:00', key='-VIDEO-DURATION-')]], pad=0),
    sg.Column([[sg.StatusBar('Pos: 00:00:00', key='-VIDEO-POSITION-')]], pad=0),
    sg.Column([[sg.StatusBar('Vol: 100', key='-VOLUME-')]], pad=0)
]


def handle_status_bar(window: sg.Window, event: str, values: dict[str, Any]):
    player = window.metadata['media_player']

    if event == '-VIDEO-LOADED-':
        duration_ms = window.metadata['duration_ms']
        filepath = window.metadata['filepath']

        window['-VIDEO-DURATION-'].update(value=f"Dur: {seconds_to_position(duration_ms / 1000).split('.')[0]}")
        window['-FILENAME-'].update(value=filepath.name)
    elif event == '-TIMELINE-' or player.is_playing():
        window['-VIDEO-POSITION-'].update(value=f"Pos: {seconds_to_position(player.get_time() / 1000).split('.')[0]}")
