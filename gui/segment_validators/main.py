import PySimpleGUI as sg

from .lib.vlc_instance import create_vlc_player

from .models.segment_container import SegmentContainer

from .views.toolbar import toolbar
from .views.status_bar import status_bar, handle_status_bar
from .views.media_control import media_control, handle_media_control
from .views.timeline import timeline, handle_timeline
from .views.segments_timeline import segments_timeline
from .views.segments_list import segments_list
from .views.video import video


def make_window():
    window = sg.Window('Segments Reviewer', layout,
                       finalize=True, resizable=True, use_default_focus=False)
    window.set_min_size(window.size)
    window.bring_to_front()
    window.force_focus()

    window.metadata = {
        'segments': SegmentContainer(),
        'vlc': create_vlc_player(window)
    }

    return window


layout = [
    [toolbar],
    [sg.Column([[
        sg.Column([video, timeline, segments_timeline, media_control],
                  element_justification='c', expand_x=True, expand_y=True, pad=0),
        sg.Column([segments_list], justification='r',
                  element_justification='r', expand_y=True, pad=0)
    ]], expand_x=True, expand_y=True, pad=0)],
    [sg.Column([[*status_bar, sg.Button('Validate and quit',
               size=(30, 0), pad=((10, 0), (0, 0)))]], expand_x=True)]
]

handlers = (
    handle_status_bar,
    handle_media_control,
    handle_timeline,
)


def main():
    window = make_window()
    window['-VID_OUT-'].expand(True, True)

    while True:
        event, values = window.read()  # type: ignore
        if event == sg.WIN_CLOSED:
            break

        for handler in handlers:
            handler(window, event, values)

    window.close()
