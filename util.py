from datetime import timedelta
import logging


def position_in_seconds(time: str) -> float:
    hours, mins, secs = time.split(':', maxsplit=3)

    return timedelta(
        hours=int(hours),
        minutes=int(mins),
        seconds=float(secs)
    ).total_seconds()


class ConsoleLoggerFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return  record.name not in ['process_movie', 'lib.backup_policy_executor'] \
            or (record.name == 'process_movie' and record.levelno > logging.INFO)
