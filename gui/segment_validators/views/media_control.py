from typing import Any
import PySimpleGUI as sg


def btn(name):
    return sg.Button(name, size=(6, 1), pad=(1, 1))


media_control = [
    sg.Column(
        [[btn('play'), btn('pause')]],
        justification='c'
    )
]


def handle_media_control(window: sg.Window, event: str, values: dict[str, Any]):
    if event in ('play', 'pause'):
        getattr(window.metadata['media_player'], event)()
