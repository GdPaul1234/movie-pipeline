from typing import Any
import PySimpleGUI as sg

def btn(name):
    return sg.Button(name, size=(6, 1), pad=(1, 1))


media_control = [btn('play'), btn('pause'), btn('stop')]


def handle_media_control(window: sg.Window, event: str, values: dict[str, Any]):
    if event in ('play', 'pause', 'stop'):
        getattr(window.metadata['vlc'].list_player, event)()
