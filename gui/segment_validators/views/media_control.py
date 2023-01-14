from typing import Any
import PySimpleGUI as sg

from util import seconds_to_position

def btn(text, /, *, key=None, size=(6,1), pad=(1,1)):
    return sg.Button(text, key=(key or text), size=size, pad=pad)


def txt(text, key):
    return sg.Column([[sg.Text(text, key=key, pad=0)]], pad=0)


def layout():
    return [
        txt('00:00:00', key='-VIDEO-POSITION-'),
        sg.Push(),
        sg.Sizer(5),
        btn('-1s', key='set_relative_position::-1', size=(3,1)),
        btn('+1s', key='set_relative_position::1', size=(3,1)),
        sg.Sizer(5),
        btn('-5s', key='set_relative_position::-5', size=(3,1)),
        btn('+5s', key='set_relative_position::5', size=(3,1)),
        sg.Sizer(5),
        btn('-15s', key='set_relative_position::-15', size=(4,1)),
        btn('+15s', key='set_relative_position::15', size=(4,1)),
        sg.Push(),
        txt('00:00:00', key='-VIDEO-DURATION-'),
    ]


def handle_media_control(window: sg.Window, event: str, values: dict[str, Any]):
    player = window.metadata['media_player']

    if isinstance(event, str) and event.startswith('set_relative_position::'):
        command, delta = event.split('::')
        window.perform_long_operation(lambda: getattr(player, command)(float(delta), window), '-TASK-DONE-')

    elif event == '-VIDEO-LOADED-':
        duration_ms = window.metadata['duration_ms']
        filepath = window.metadata['filepath']

        window['-VIDEO-DURATION-'].update(value=seconds_to_position(duration_ms / 1000).split('.')[0])
        window['-FILENAME-'].update(value=filepath.name)

    elif event in('-TIMELINE-', '-VIDEO-NEW-POSITION-'):
        position = window.metadata['position_ms'] / 1000
        window['-VIDEO-POSITION-'].update(value=seconds_to_position(position).split('.')[0])
