import logging
import re
from subprocess import Popen
import subprocess
from typing import IO, cast, TypedDict
import ffmpeg

logger = logging.getLogger(__name__)

# reference: https://github.com/jonghwanhyeon/python-ffmpeg/blob/main/ffmpeg/utils.py#L12-L14
progress_pattern = re.compile(
    r'(frame|fps|size|time|bitrate|speed)\s*\=\s*(\S+)')


class ProgressItem(TypedDict):
    frame: str
    fps: str
    size: str
    time: str
    speed: str


def ffmpeg_command_with_progress(command, cmd=['ffmpeg'], **args):
    with subprocess.Popen(command.compile(cmd=cmd), **args, text= True, stderr=subprocess.PIPE) as process:
        while True:
            line = cast(IO[str], process.stderr).readline().strip()

            if process.poll() is not None:
                break

            if line:
                logger.debug(line)

                if items := {key: value
                            for key, value in progress_pattern.findall(line) if value != 'N/A'}:
                    yield cast(ProgressItem, items)
