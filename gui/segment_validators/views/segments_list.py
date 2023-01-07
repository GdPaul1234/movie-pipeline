import PySimpleGUI as sg

segments_list = [
    sg.Table(
        values=[['0:00:00', '0:00:00', '00:00']],
        headings=('Start', 'End', 'Duration'),
        enable_events=True,
        enable_click_events=True,
        expand_y=True,
        key='-TABLE-'
    )
]
