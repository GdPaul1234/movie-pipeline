import PySimpleGUI as sg

from ..models.keys import STATUS_BAR_KEY


def layout():
    return [
        sg.StatusBar('Open a file to get started'.ljust(80), key=STATUS_BAR_KEY, pad=0),
    ]
