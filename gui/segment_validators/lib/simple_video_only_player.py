import logging
from pathlib import Path
from threading import Event
import time
from typing import cast
from deffcode import Sourcer
import PySimpleGUI as sg
import numpy as np
import ffmpeg
import cv2


logger = logging.getLogger(__name__)

def extract_frame(stream, position_s, width, height):
    out, _ = (
        stream
        .output('pipe:', format='rawvideo', pix_fmt='bgr24', vframes=1)
        .run(cmd=['ffmpeg', '-ss', str(position_s)], capture_stdout=True, capture_stderr=True)
    )

    return np.frombuffer(out, np.uint8).reshape([height, width, 3])


class SimpleVideoOnlyPlayerConsumer:
    def __init__(self, source: Path) -> None:
        self._source = source
        self._current_position = 0.
        self._stop_event = Event()

        sourcer = Sourcer(str(source)).probe_stream()
        self._metadata = cast(dict, sourcer.retrieve_metadata())

    def play(self, window: sg.Window):
        logger.debug('Play "%s" from %fs', self._source, self._current_position)

        duration = self._metadata['source_duration_sec']

        self._stop_event.clear()

        while not self._stop_event.is_set():
            if self._current_position - 4 >= duration:
                self._current_position = 0.
                break

            self.set_relative_position(1, window)
            # time.sleep(.04)


    def pause(self, window: sg.Window|None = None):
        logger.debug('Pause "%s"', self._source)
        self._stop_event.set()

    def set_position(self, position: float, window: sg.Window):
        self._current_position = position


        stream = ffmpeg.input(str(self._source))
        frame = extract_frame(stream, self._current_position, *self._metadata['source_video_resolution'])

        if frame is not None:
            encoded_frame = cv2.imencode('.png', cv2.resize(frame, (480, 270)))[1].tobytes()
            logger.debug(self._current_position)
            window.write_event_value('-VIDEO-NEW-FRAME-', encoded_frame)
            window.write_event_value('-VIDEO-NEW-POSITION-', self._current_position)

    def set_relative_position(self, delta: float, window: sg.Window):
        self._current_position += delta
        self.set_position(self._current_position, window)
