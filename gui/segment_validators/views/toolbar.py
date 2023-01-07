import PySimpleGUI as sg

toolbar = sg.Column([[
    sg.Text('Review the segments in the right, then click on "Validate and quit"', font='Any 12'),
    sg.Combo([], enable_events=True, size=(33,0), pad=((10,0), (0,0)), key='-DETECTOR-')
]], justification='r')
