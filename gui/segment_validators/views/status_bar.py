import PySimpleGUI as sg


def layout():
    return [
        sg.StatusBar('Open a file to get started', key='-FILENAME-', pad=((0, 5), (0, 0))),
        sg.Column([[sg.StatusBar('Vol: 100', key='-VOLUME-', pad=0)]], pad=0)
    ]
