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
