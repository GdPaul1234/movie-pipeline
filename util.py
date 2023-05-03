from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
import logging
import time
import ffmpeg


def position_in_seconds(time: str) -> float:
    hours, mins, secs = time.split(':', maxsplit=3)

    return timedelta(
        hours=int(hours),
        minutes=int(mins),
        seconds=float(secs)
    ).total_seconds()


def seconds_to_position(seconds: float) -> str:
    formatted_time = time.strftime('%H:%M:%S', time.gmtime(seconds))
    formatted_decimal_part = f'{(seconds % 1):.3f}'.removeprefix('0')
    return f"{formatted_time}{formatted_decimal_part}"


def total_movie_duration(movie_file_path: Path|str) -> float:
        probe = ffmpeg.probe(str(movie_file_path))

        video_streams = [stream for stream in probe['streams']
                         if stream.get('codec_type', 'N/A') == 'video']

        return float(video_streams[0]['duration'])


@contextmanager
def diff_tracking(mut_prev_value: list[float], current_value: float):
    prev_value, = mut_prev_value
    yield current_value - prev_value
    mut_prev_value[0] = current_value


def timed_run(func, *args, **kwargs):
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()

    return result, end_time - start_time


class ConsoleLoggerFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name not in [
            'movie_pipeline.commands.process_movie',
            'movie_pipeline.lib.backup_policy_executor'
        ] or record.levelno > logging.INFO
