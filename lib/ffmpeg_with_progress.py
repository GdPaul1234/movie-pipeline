import re
from subprocess import Popen
from typing import IO, cast, TypedDict


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
    with cast(Popen[bytes], command.run_async(**args, pipe_stderr=True)) as process:
        while True:
            line = cast(IO[bytes], process.stderr).readline()

            if process.poll() is not None:
                break

            if line:
                if items := {key: value
                            for key, value in progress_pattern.findall(line.strip().decode()) if value != 'N/A'}:
                    yield cast(ProgressItem, items)
