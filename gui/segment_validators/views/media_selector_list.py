import PySimpleGUI as sg

from ..models.keys import MEDIA_SELECTOR_KEY


def layout():
    return [
        sg.Listbox(
            values=[],
            key=MEDIA_SELECTOR_KEY,
            enable_events= True,
            expand_x=True,
            expand_y=True
        )
    ]
