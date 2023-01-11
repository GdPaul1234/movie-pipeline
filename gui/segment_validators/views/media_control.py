from typing import Any
import PySimpleGUI as sg

from util import seconds_to_position

def btn(name, /, *, key=None):
    return sg.Button(name, key=(key or name), size=(6, 1), pad=(1, 1))


def txt(text, key):
    return sg.Column([[sg.Text(text, key=key, pad=0)]], pad=0)


media_control = [
    txt('00:00:00', key='-VIDEO-POSITION-'),
    sg.Push(),
    btn('play'), btn('pause'),
    sg.Sizer(0,5), btn('>|', key='next_frame'),
    sg.Push(),
    txt('00:00:00', key='-VIDEO-DURATION-'),
]


def handle_media_control(window: sg.Window, event: str, values: dict[str, Any]):
    player = window.metadata['media_player']

    if event in ('play', 'pause', 'next_frame'):
        getattr(window.metadata['media_player'], event)()

    elif event == '-VIDEO-LOADED-':
        duration_ms = window.metadata['duration_ms']
        filepath = window.metadata['filepath']

        window['-VIDEO-DURATION-'].update(value=seconds_to_position(duration_ms / 1000).split('.')[0])
        window['-FILENAME-'].update(value=filepath.name)

    elif event == '-TIMELINE-' or player.is_playing():
        window['-VIDEO-POSITION-'].update(value=seconds_to_position(player.get_time() / 1000).split('.')[0])
