from typing import Any, cast

import PySimpleGUI as sg
from decoratorOperations import debounce
from PIL import Image, ImageTk
from PIL.Image import Resampling

from ..models.context import SegmentValidatorContext
from ..models.events import VIDEO_NEW_FRAME_EVENT
from ..models.keys import VIDEO_CONTAINER_KEY, VIDEO_OUT_KEY


@debounce(.1)
def rerender_video(window: sg.Window, _event: str, values: dict[str, Any]):
    metadata = cast(SegmentValidatorContext, window.metadata)
    metadata.media_player.set_position(metadata.position, window)


def render_video_new_frame(window: sg.Window, _event: str, values: dict[str, Any]):
    image_container = cast(sg.Image, window[VIDEO_OUT_KEY])
    video_frame = cast(sg.Frame, window[VIDEO_CONTAINER_KEY])

    size, frame = values[VIDEO_NEW_FRAME_EVENT]
    container_size = video_frame.get_size()
    container_width = container_size[0] or 480

    new_width = round(.95*container_width)
    new_height = round(new_width * (size[1] / size[0]))

    image = Image.frombytes(mode='RGB', size=size, data=frame)
    image_container.update(data=ImageTk.PhotoImage(
        image.resize((new_width, new_height), resample=Resampling.NEAREST)
    ))

