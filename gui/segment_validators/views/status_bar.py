import PySimpleGUI as sg


def layout():
    return [
        sg.StatusBar('Open a file to get started', key='-FILENAME-', pad=0),
    ]
