from typing import Any
import PySimpleGUI as sg


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


def handle_timeline(window: sg.Window, event: str, values: dict[str, Any]):
    media_player = window.metadata['media_player']
    duration_ms = window.metadata['duration_ms']

    if event == '-VIDEO-LOADED-':
        window['-TIMELINE-'].update(value=0, range=(0, duration_ms))

    elif event == '-TIMELINE-':
        new_position = int(values['-TIMELINE-'])
        media_player.set_time(new_position)

    elif media_player.is_playing():
        window['-TIMELINE-'].update(value=media_player.get_time())
