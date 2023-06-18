from typing import Any
import PySimpleGUI as sg

from ..models.events import TIMELINE_POSTION_UPDATED_EVENT, VIDEO_LOADED_EVENT, VIDEO_POSITION_UPDATED_EVENT
from ..models.keys import VIDEO_DURATION_LABEL_KEY, VIDEO_POSITION_LABEL_KEY
from ..controllers.media_control_controller import goto_selected_segment, set_relative_position, set_video_information, update_video_position


def btn(text, /, *, key=None, size=(6,1), pad=(1,1)):
    return sg.Button(text, key=(key or text), size=size, pad=pad)


def txt(text, key):
    return sg.Column([[sg.Text(text, key=key, pad=0)]], pad=0)

handlers = {
    VIDEO_LOADED_EVENT: set_video_information,
    VIDEO_POSITION_UPDATED_EVENT: update_video_position,
    TIMELINE_POSTION_UPDATED_EVENT: update_video_position,
    'goto_selected_segment': goto_selected_segment,
    'set_relative_position': set_relative_position,
}


def layout():
    return [
        txt('00:00:00', key=VIDEO_POSITION_LABEL_KEY),
        sg.Push(),
        btn('>[-', key='goto_selected_segment::start', size=(3,1)),
        btn('-]<', key='goto_selected_segment::end', size=(3,1)),
        sg.Sizer(5),
        btn('-1s', key='set_relative_position::-1', size=(3,1)),
        btn('+1s', key='set_relative_position::1', size=(3,1)),
        sg.Sizer(5),
        btn('-5s', key='set_relative_position::-5', size=(3,1)),
        btn('+5s', key='set_relative_position::5', size=(3,1)),
        sg.Sizer(5),
        btn('-15s', key='set_relative_position::-15', size=(4,1)),
        btn('+15s', key='set_relative_position::15', size=(4,1)),
        sg.Push(),
        txt('00:00:00', key=VIDEO_DURATION_LABEL_KEY),
    ]


def handle_media_control(window: sg.Window, event: str, values: dict[str, Any]):
    if isinstance(event, str) and (evt := event.split('::')[0]) in handlers.keys():
        handlers[evt](window, event, values)
