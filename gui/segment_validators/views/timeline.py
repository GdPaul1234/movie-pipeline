from typing import Any
import PySimpleGUI as sg

from ..models.events import VIDEO_LOADED_EVENT, VIDEO_POSITION_UPDATED_EVENT, TIMELINE_POSTION_UPDATED_EVENT
from ..models.keys import TIMELINE_SLIDER_KEY
from ..controllers.timeline_controller import init_timeline_slider, seek_to_position, update_timeline_slider

def layout():
    return [
        sg.Slider(
            (0, 0),
            0,
            orientation='h',
            enable_events=True,
            disable_number_display=True,
            expand_x=True,
            pad=0,
            key=TIMELINE_SLIDER_KEY
        )
    ]


handlers = {
    VIDEO_LOADED_EVENT: init_timeline_slider,
    TIMELINE_POSTION_UPDATED_EVENT: seek_to_position,
    VIDEO_POSITION_UPDATED_EVENT: update_timeline_slider
}


def handle_timeline(window: sg.Window, event: str, values: dict[str, Any]):
    if event in handlers.keys():
        handlers[event](window, event, values)
