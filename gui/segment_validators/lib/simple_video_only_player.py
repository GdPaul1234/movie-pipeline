import logging
from pathlib import Path
from typing import cast

import ffmpeg
import PySimpleGUI as sg
from deffcode import Sourcer

from ..lib.video_player import IVideoPlayer
from ..models.events import VIDEO_NEW_FRAME_EVENT, VIDEO_POSITION_UPDATED_EVENT

logger = logging.getLogger(__name__)

def extract_frame(stream, position_s):
    out, _ = (
        stream
        .output('pipe:', format='rawvideo', pix_fmt='rgb24', vframes=1)
        .run(cmd=['ffmpeg', '-ss', str(position_s)], capture_stdout=True, capture_stderr=True)
    )

    return out


class SimpleVideoOnlyPlayerConsumer(IVideoPlayer):
    def __init__(self, source: Path) -> None:
        self._source = source
        self._current_position = 0.

        sourcer = Sourcer(str(source)).probe_stream()
        self._metadata = cast(dict, sourcer.retrieve_metadata())
        self._duration = self._metadata['source_duration_sec']
        self._size = self._metadata['source_video_resolution']

    @property
    def position(self):
        return self._current_position

    @property
    def duration(self):
        return self._duration

    def set_position(self, position: float, window: sg.Window):
        self._current_position = position

        stream = ffmpeg.input(str(self._source))
        frame = extract_frame(stream, self._current_position)

        if self._current_position < 0 or self._current_position >= (self._duration - 1):
            self._current_position = 0.
            window.write_event_value(VIDEO_POSITION_UPDATED_EVENT, 0.)
            return

        if frame is not None:
            logger.debug(self._current_position)
            window.write_event_value(VIDEO_NEW_FRAME_EVENT, (self._size, frame))
            window.write_event_value(VIDEO_POSITION_UPDATED_EVENT, self._current_position)

    def set_relative_position(self, delta: float, window: sg.Window):
        self.set_position(self._current_position + delta, window)

