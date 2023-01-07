import PySimpleGUI as sg

status_bar = [
    sg.StatusBar('Open a file to get started', key='-FILENAME-', pad=((0,5),(0,0))),
    sg.Column([[sg.StatusBar('Dur: 00:00:00', key='-VIDEO-Duration-')]], pad=0),
    sg.Column([[sg.StatusBar('Pos: 00:00:00', key='-VIDEO-POSITION-')]], pad=0),
    sg.Column([[sg.StatusBar('Vol: 100', key='-VOLUME-')]], pad=0)
]
