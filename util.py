from contextlib import contextmanager
from datetime import timedelta
import logging


def position_in_seconds(time: str) -> float:
    hours, mins, secs = time.split(':', maxsplit=3)

    return timedelta(
        hours=int(hours),
        minutes=int(mins),
        seconds=float(secs)
    ).total_seconds()

@contextmanager
def diff_tracking(mut_prev_value: list[float], current_value: float):
    prev_value, = mut_prev_value
    yield current_value - prev_value
    mut_prev_value[0] = current_value

class ConsoleLoggerFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return  record.name not in ['commands.process_movie', 'lib.backup_policy_executor'] \
            or record.levelno > logging.INFO
