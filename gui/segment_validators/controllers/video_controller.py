from typing import Any, cast

import PySimpleGUI as sg
from decoratorOperations import throttle
from PIL import Image, ImageTk
from PIL.Image import Resampling

from ..models.context import SegmentValidatorContext
from ..models.events import VIDEO_NEW_FRAME_EVENT
from ..models.keys import VIDEO_CONTAINER_KEY, VIDEO_OUT_KEY


@throttle(2)
def _rerender_video_after_resizing(window: sg.Window):
    metadata = cast(SegmentValidatorContext, window.metadata)
    metadata.media_player.set_position(metadata.position, window)


def _compute_size(window: sg.Window, size: tuple[int, int]):
    video_frame = cast(sg.Frame, window[VIDEO_CONTAINER_KEY])

    container_size = video_frame.get_size()
    container_width = container_size[0] or 480

    new_width = round(.95*container_width)
    new_height = round(new_width * (size[1] / size[0]))

    return (new_width, new_height)


def rerender_video(window: sg.Window, _event: str, _values: dict[str, Any]):
    image_container = cast(sg.Image, window[VIDEO_OUT_KEY])
    black_image = Image.new(mode='RGB', size=_compute_size(window, (1920, 1080)))
    image_container.update(data=ImageTk.PhotoImage(black_image))
    _rerender_video_after_resizing(window)


def render_video_new_frame(window: sg.Window, _event: str, values: dict[str, Any]):
    image_container = cast(sg.Image, window[VIDEO_OUT_KEY])
    size, frame = values[VIDEO_NEW_FRAME_EVENT]

    image = Image.frombytes(mode='RGB', size=size, data=frame)
    new_size = _compute_size(window, size)
    image_container.update(data=ImageTk.PhotoImage(image.resize(new_size, resample=Resampling.NEAREST)))

