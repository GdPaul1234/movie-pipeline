import logging
from pathlib import Path
from threading import Event
import time
from typing import cast
from deffcode import Sourcer
import PySimpleGUI as sg
import ffmpeg


logger = logging.getLogger(__name__)

def extract_frame(stream, position_s):
    out, _ = (
        stream
        .output('pipe:', format='rawvideo', pix_fmt='rgb24', vframes=1)
        .run(cmd=['ffmpeg', '-ss', str(position_s)], capture_stdout=True, capture_stderr=True)
    )

    return out


class SimpleVideoOnlyPlayerConsumer:
    def __init__(self, source: Path) -> None:
        self._source = source
        self._current_position = 0.
        self._stop_event = Event()

        sourcer = Sourcer(str(source)).probe_stream()
        self._metadata = cast(dict, sourcer.retrieve_metadata())
        self._duration = self._metadata['source_duration_sec']
        self._size = self._metadata['source_video_resolution']

    def play(self, window: sg.Window):
        logger.debug('Play "%s" from %fs', self._source, self._current_position)
        fps = self._metadata['source_video_framerate']
        self._stop_event.clear()

        while not self._stop_event.is_set():
            if self._current_position >= (self._duration - 1):
                self._current_position = 0.
                break

            self.set_relative_position(3/fps, window)
            time.sleep(1/fps)


    def pause(self, window: sg.Window|None = None):
        logger.debug('Pause "%s"', self._source)
        self._stop_event.set()

    def set_position(self, position: float, window: sg.Window):
        self._current_position = position

        stream = ffmpeg.input(str(self._source))
        frame = extract_frame(stream, self._current_position)

        if self._current_position < 0 or self._current_position >= (self._duration - 1):
            self._current_position = 0.
            return

        if frame is not None:
            logger.debug(self._current_position)
            window.write_event_value('-VIDEO-NEW-FRAME-', (self._size, frame))
            window.write_event_value('-VIDEO-NEW-POSITION-', self._current_position)

    def set_relative_position(self, delta: float, window: sg.Window):
        self._current_position += delta
        self.set_position(self._current_position, window)

