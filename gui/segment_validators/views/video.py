from typing import Any, cast
import PySimpleGUI as sg
from PIL import Image, ImageTk
from PIL.Image import Resampling
from decoratorOperations import debounce


def layout():
    return [
        sg.Frame(
            '',
            [[sg.Image('', size=(480, 270), pad=0, key='-VID-OUT-')]],
            expand_x=True, expand_y=True,
            element_justification='c',
             pad=0,
            key='-VIDEO-FRAME-'
        )
    ]


@debounce(.1)
def rerender_video(media_player,window: sg.Window):
    new_position = window.metadata['position_ms'] / 1000
    media_player.set_position(new_position, window)


def handle_video(window: sg.Window, event: str, values: dict[str, Any]):
    media_player = window.metadata['media_player']

    image_container = cast(sg.Image, window['-VID-OUT-'])
    video_frame = cast(sg.Frame, window['-VIDEO-FRAME-'])

    if event == '-VIDEO-NEW-FRAME-':
        size, frame = values['-VIDEO-NEW-FRAME-']
        container_size = video_frame.get_size()
        container_width = container_size[0] or 480

        new_width = round(.95*container_width)
        new_height = round(new_width * (size[1] / size[0]))

        image = Image.frombytes(mode='RGB', size=size, data=frame)
        image_container.update(data=ImageTk.PhotoImage(
            image.resize((new_width, new_height),
                         resample=Resampling.NEAREST)
        ))

    elif event == '-CONFIGURE-':
        rerender_video(media_player, window)
