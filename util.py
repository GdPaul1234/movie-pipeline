import logging
import time
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Iterator

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


def progress_to_task_iterator(progress_iterator: Iterator[float], count=100) -> Iterator[int]:
    """
    Take a progress iterator (value is increasing from 0.0 to 1.0)
    and convert it for use with multiprocessing library that can track the progress
    of a list of tasks but not the task individually.

    It returns an iterable that yield value at the progress frequency.

    Args:
        progress_iterator (Iterator[float]): iterator of float that increase from 0.0 to 1.0
        count (int, optional): Expected task count. Defaults to 100.

    Yields:
        Iterator[int]: Iterator that return a result similar to range(count + 2)
    """
    task_number, task_reminder = divmod(0, count)

    for progress in progress_iterator:
        if progress == 1.0:
            for x in range(task_number, count + 1):
                yield x
        else:
            current_task_number, current_task_reminder = divmod(int(count*progress), count)
            current_task_number += task_reminder

            for x in range(task_number, current_task_number):
                yield x

            task_number, task_reminder = current_task_number, current_task_reminder


class ConsoleLoggerFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name not in [
            'movie_pipeline.services.movie_file_processor',
            'movie_pipeline.lib.backup_policy_executor'
        ] or record.levelno > logging.INFO
