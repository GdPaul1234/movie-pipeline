from typing import IO, cast, TypedDict
import logging
import re
import subprocess
import ffmpeg

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


def ffmpeg_command_with_progress(command, cmd=['ffmpeg'], keep_log=False, line_filter=FFmpegLineFilter(), **args):
    lines = []

    with subprocess.Popen(command.compile(cmd=cmd), **args, text=True, stderr=subprocess.PIPE) as process:
        for line in cast(IO[str], process.stderr):
            if (retcode := process.poll()) is not None:
                if retcode != 0:
                    raise ffmpeg.Error('ffmpeg', None, line)
                break

            if keep_log and line_filter.filter(line):
                logger.info(line)
                lines.append(line)
            else:
                logger.debug(line)

            if items := {key: value
                        for key, value in progress_pattern.findall(line) if value != 'N/A'}:
                yield cast(ProgressItem, items)

        return lines
