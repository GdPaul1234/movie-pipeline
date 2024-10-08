import json
import logging
import re
import subprocess
from collections import deque
from multiprocessing import Event
from pathlib import Path
from typing import IO, TypedDict, cast

import ffmpeg

from ...lib.ffmpeg.ffmpeg_cli_presets import get_ffprefixes
from ...settings import Settings

logger = logging.getLogger(__name__)

# reference: https://github.com/jonghwanhyeon/python-ffmpeg/blob/main/ffmpeg/utils.py#L12-L14
progress_pattern = re.compile(r'(frame|fps|size|time|bitrate|speed)\s*\=\s*(\S+)')
match_all_pattern = re.compile('')


class ProgressItem(TypedDict):
    frame: str
    fps: str
    size: str
    time: str
    speed: str


class FFmpegLineFilter:
    def __init__(self, filter_pattern = match_all_pattern) -> None:
        self._filter_pattern = filter_pattern

    def filter(self, line: str) -> bool:
        return self._filter_pattern.search(line) is not None


class FFmpegLineContainer:
    def __init__(self) -> None:
        self._lines = []

    @property
    def lines(self) -> list[str]:
        return self._lines

    def append(self, line: str):
        logger.debug(line)
        self._lines.append(line)


def ffmpeg_command_with_progress(
    command, cmd=['ffmpeg'],
    keep_log=False,
    line_filter=FFmpegLineFilter(),
    line_container=FFmpegLineContainer(),
    stop_signal=Event(),
    **kwargs
):
    with subprocess.Popen(command.compile(cmd=cmd), **kwargs, text=True, stderr=subprocess.PIPE) as process:
        last_lines: deque[str] = deque([], 50)

        for line in cast(IO[str], process.stderr):
            last_lines.append(line)

            try:
                if (retcode := process.poll()) is not None:
                    if retcode != 0:
                        raise ffmpeg.Error('ffmpeg', None, '\n'.join(last_lines))
                    break

                if stop_signal.is_set():
                    logger.info('Killing')
                    raise InterruptedError

                line_container.append(line) if keep_log and line_filter.filter(line) else logger.debug(line)

                if items := {key: value
                             for key, value in progress_pattern.findall(line) if value != 'N/A'}:
                    yield ProgressItem(**items)

            except InterruptedError as e:
                logger.exception(e)
                process.terminate()

            except Exception as e:
                logger.error(last_lines)
                logger.exception(e)
                process.terminate()
                raise e

        return line_container.lines


def ffmpeg_frame_producer(
    input: Path, 
    target_fps: float, 
    config: Settings, 
    other_video_filter='',
    custom_ffparams={}
):
    from deffcode import FFdecoder

    ffparams = {
        "-vcodec": None,  # skip any decoder and let FFmpeg chose
        "-ffprefixes": get_ffprefixes(config.ffmpeg_hwaccel),
        "-custom_resolution": "null",  # discard `-custom_resolution`
        "-framerate": "null",  # discard `-framerate`
        # define your filters
        "-vf":  ','.join(filter(bool, [f"fps={target_fps}", other_video_filter])),
        **custom_ffparams
    }

    with FFdecoder(str(input), frame_format='gray', **ffparams, custom_ffmpeg=str(config.ffmpeg_path)) as decoder:
        metadata = json.loads(decoder.metadata)

        frame_pos = 0
        seconds_pos = 0
        frame_count = metadata['approx_video_nframes']

        for frame in decoder.generateFrame():
            try:
                if frame_pos >= (frame_count - 100):
                    break

                frame_pos += 1
                seconds_pos = frame_pos / target_fps

                yield frame, frame_pos, seconds_pos

            except KeyboardInterrupt:
                break
