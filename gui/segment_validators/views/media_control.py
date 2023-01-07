import PySimpleGUI as sg

def btn(name):
    return sg.Button(name, size=(6, 1), pad=(1, 1))

media_control = [btn('play'), btn('pause'), btn('stop')]
