import PySimpleGUI as sg

detector_selector = [
    sg.Combo(
        [],
        enable_events=True,
        size=(33,0),
        pad=((0,0), (5,5)),
        key='-DETECTOR-'
    )
]
