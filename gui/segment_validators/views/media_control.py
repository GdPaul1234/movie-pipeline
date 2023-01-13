from typing import Any
import PySimpleGUI as sg

from util import seconds_to_position

def btn(name, /, *, key=None):
    return sg.Button(name, key=(key or name), size=(6, 1), pad=(1, 1))


def txt(text, key):
    return sg.Column([[sg.Text(text, key=key, pad=0)]], pad=0)


def layout():
    return [
        txt('00:00:00', key='-VIDEO-POSITION-'),
        sg.Push(),
        btn('play'), btn('pause'),
        sg.Push(),
        txt('00:00:00', key='-VIDEO-DURATION-'),
    ]


def handle_media_control(window: sg.Window, event: str, values: dict[str, Any]):
    if event in ('play', 'pause'):
        window.perform_long_operation(lambda: getattr(window.metadata['media_player'], event)(window), '-TASK-DONE-')

    elif event == '-VIDEO-LOADED-':
        duration_ms = window.metadata['duration_ms']
        filepath = window.metadata['filepath']

        window['-VIDEO-DURATION-'].update(value=seconds_to_position(duration_ms / 1000).split('.')[0])
        window['-FILENAME-'].update(value=filepath.name)

    elif event in('-TIMELINE-', '-VIDEO-NEW-POSITION-'):
        position = window.metadata['position_ms'] / 1000
        window['-VIDEO-POSITION-'].update(value=seconds_to_position(position).split('.')[0])
