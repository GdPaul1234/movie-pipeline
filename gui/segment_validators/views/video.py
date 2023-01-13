from typing import Any, cast
import PySimpleGUI as sg
import cv2


def layout():
    return [sg.Image('', size=(480, 270), key='-VID-OUT-')]


def handle_video(window: sg.Window, event: str, values: dict[str, Any]):
    image = cast(sg.Image, window['-VID-OUT-'])

    if event == '-VIDEO-NEW-FRAME-':
        image.update(data=values['-VIDEO-NEW-FRAME-'])
