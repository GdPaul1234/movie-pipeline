from pathlib import Path
import time
import PySimpleGUI as sg
import vlc

from .lib.vlc_instance import create_vlc_player

from .models.segment_container import SegmentContainer

from .views.detector_selector import detector_selector
from .views.status_bar import status_bar, handle_status_bar
from .views.media_control import media_control, handle_media_control
from .views.timeline import timeline, handle_timeline
from .views.segments_timeline import segments_timeline
from .views.segments_list import segments_list
from .views.video import video


def make_window():
    window = sg.Window('Segments Reviewer', layout, finalize=True, resizable=True, use_default_focus=False)
    window.set_min_size(window.size)
    window.bring_to_front()
    window.force_focus()

    window.metadata = {
        'segments': SegmentContainer(),
        'media_player': create_vlc_player(window),
        'filepath': Path(''),
        'duration_ms': 0
    }

    return window


def load_media(window: sg.Window, filepath: Path):
    media_player = window.metadata['media_player']

    media = vlc.Media(filepath)
    media_player.set_media(media)

    media_player.play()
    time.sleep(0.5)
    duration_ms = media_player.get_length()
    media_player.pause()

    window.metadata['duration_ms'] = duration_ms
    window.metadata['filepath'] = filepath
    window.write_event_value('-VIDEO-LOADED-', True)


left_col = [
    video, timeline, segments_timeline, media_control,
    status_bar,
]

right_col = [
    detector_selector,
    segments_list,
    [sg.Button('Validate and quit', size=(30, 0), pad=((0,0), (5,0)))]
]

layout = [
    [sg.Column([[
        sg.Text('Review the segments in the right, then click on "Validate and quit"', font='Any 12'),
    ]], element_justification='c', expand_x=True)],
    [sg.Column([[
        sg.Column(left_col, expand_x=True, expand_y=True, pad=0),
        sg.Column(right_col, expand_y=True, pad=0),
    ]], element_justification='c', expand_x=True, expand_y=True)]
]

handlers = (
    handle_status_bar,
    handle_media_control,
    handle_timeline,
)


def main(filepath: Path):
    window = make_window()

    load_media(window, filepath)
    window['-VID_OUT-'].expand(True, True)

    while True:
        event, values = window.read(timeout=500)  # type: ignore
        if event == sg.WIN_CLOSED:
            break

        for handler in handlers:
            handler(window, event, values)

    window.close()
