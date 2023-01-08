from typing import Any
import PySimpleGUI as sg

timeline = [
    sg.Slider(
        (0, 0),
        0,
        orientation='h',
        enable_events=True,
        disable_number_display=True,
        expand_x=True,
        key='-MEDIA-SLIDER-'
    )
]


def handle_timeline(window: sg.Window, event: str, values: dict[str, Any]):
    player = window.metadata['vlc'].player

    if event == '-VIDEO-LOADED-':
        window['-MEDIA-SLIDER-'].update(value=0, range=(0, player.get_length()))
    elif event == '-MEDIA-SLIDER-':
        new_position = values['-MEDIA-SLIDER-']
        player.set_position(new_position)
    elif player.is_playing():
        window['-MEDIA-SLIDER-'].update(value=player.get_time())
