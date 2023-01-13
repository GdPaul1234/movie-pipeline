from typing import Any
import PySimpleGUI as sg
from decoratorOperations import debounce


def layout():
    return [
        sg.Slider(
            (0, 0),
            0,
            orientation='h',
            enable_events=True,
            disable_number_display=True,
            expand_x=True,
            pad=0,
            key='-TIMELINE-'
        )
    ]

@debounce(0.1)
def seek_to_position(media_player, new_position, window):
    media_player.set_position(new_position, window)


def handle_timeline(window: sg.Window, event: str, values: dict[str, Any]):
    media_player = window.metadata['media_player']
    duration_ms = window.metadata['duration_ms']

    if event == '-VIDEO-LOADED-':
        window['-TIMELINE-'].update(value=0, range=(0, duration_ms))

    elif event == '-TIMELINE-':
        new_position = values['-TIMELINE-'] / 1000
        seek_to_position(media_player, new_position, window)

    elif event == '-VIDEO-NEW-POSITION-':
        position_ms = window.metadata['position_ms'] = 1000 * values['-VIDEO-NEW-POSITION-']
        window['-TIMELINE-'].update(value=position_ms)
