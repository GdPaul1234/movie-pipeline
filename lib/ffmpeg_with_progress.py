import re
from subprocess import Popen
from typing import cast, TypedDict

# reference: https://github.com/jonghwanhyeon/python-ffmpeg/blob/main/ffmpeg/utils.py#L12-L14
progress_pattern = re.compile(
    r'(frame|fps|size|time|bitrate|speed)\s*\=\s*(\S+)')


class ProgressItem(TypedDict):
    frame: str
    fps: str
    size: str
    time: str
    speed: str


def ffmpeg_command_with_progress(command, **args):
    process = cast(Popen[bytes], command.run_async(**args, pipe_stderr=True))
    _, error = process.communicate()

    for line in error.decode().splitlines():
        items = { key: value
                  for key, value in progress_pattern.findall(line) if value != 'N/A' }

        if items:
            yield cast(ProgressItem, items)
