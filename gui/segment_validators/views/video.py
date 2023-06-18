from typing import Any
import PySimpleGUI as sg

from ..models.events import CONFIGURE_EVENT, VIDEO_NEW_FRAME_EVENT
from ..models.keys import VIDEO_OUT_KEY, VIDEO_CONTAINER_KEY
from ..controllers.video_controller import rerender_video, render_video_new_frame


def layout():
    return [
        sg.Frame(
            '',
            [[sg.Image('', size=(480, 270), pad=0, key=VIDEO_OUT_KEY)]],
            expand_x=True, expand_y=True,
            element_justification='c',
             pad=0,
            key=VIDEO_CONTAINER_KEY
        )
    ]


handlers = {
    VIDEO_NEW_FRAME_EVENT: render_video_new_frame,
    CONFIGURE_EVENT: rerender_video
}



def handle_video(window: sg.Window, event: str, values: dict[str, Any]):
    if event in handlers.keys():
        handlers[event](window, event, values)
