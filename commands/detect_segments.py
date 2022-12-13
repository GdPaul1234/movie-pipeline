import logging
from typing import Literal
from pathlib import Path
from abc import ABC
from rich.progress import Progress
import re
import yaml
import ffmpeg

from lib.ffmpeg_with_progress import ffmpeg_command_with_progress
from lib.ui_factory import transient_task_progress
from util import position_in_seconds, total_movie_duration

logger = logging.getLogger(__name__)

class BaseDetect(ABC):
    detect_filter: str
    media: Literal['audio', 'video']
    filter_pattern = re.compile('')
    args = {}

    def __init__(self, movie_path: Path) -> None:
        self._movie_path = movie_path

    def _filter_out(self, output: list[str]) -> list[str]:
        return [line for line in output if self.filter_pattern.search(line)]

    def _map_out(self, output: list[str]):
        return [{key.split('_')[1]: value
                 for key, value in self.filter_pattern.findall(line)}
                for line in output]

    def detect(self):
        in_file = ffmpeg.input(str(self._movie_path))
        total_duration = total_movie_duration(self._movie_path)

        command = (
            getattr(in_file, self.media)
            .filter_(self.detect_filter, **self.args)
            .output('-', format='null')
        )

        logger.info('Running: %s', command.compile())
        detection_result = []

        with Progress() as progress:
             with transient_task_progress(progress, description=self.detect_filter, total=total_duration) as task_id:
                process = ffmpeg_command_with_progress(command, cmd=['ffmpeg', '-hwaccel', 'cuda'], keep_log=True)

                try:
                    while True:
                        if (item := next(process)).get('time'):
                            processed_time = position_in_seconds(item['time'])
                            progress.update(task_id, completed=processed_time)
                except StopIteration as e:
                    detection_result = self._map_out(self._filter_out(e.value))

        logger.info(detection_result)
        return detection_result


class BlackDetect(BaseDetect):
    detect_filter = 'blackdetect'
    media = 'video'
    filter_pattern = re.compile(r'(black_start|black_end|black_duration)\s*\:\s*(\S+)')


class SilenceDetect(BaseDetect):
    detect_filter = 'silencedetect'
    media = 'audio'
    filter_pattern = re.compile(r'(silence_start|silence_end|silence_duration)\s*\:\s*(\S+)')

    def _map_out(self, output: list[str]):
        grouped_output = zip(*[iter(output)]*2)
        flattened_ouput = [f'{start} {end}' for start, end in grouped_output] # type: ignore
        return super()._map_out(flattened_ouput)


def run_segment_detectors(movie_path: Path):
    detectors = {
        'black': BlackDetect,
        'silence': SilenceDetect
    }
    detected_segments = {}

    for detector_key, detector_value in detectors.items():
        logger.info('Running %s detection...', detector_key)

        detector_instance = detector_value(movie_path)
        detected_segments[detector_key] = detector_instance.detect()

    return detected_segments

def command(options, config):
    logger.debug('args: %s', vars(options))
    movie_path = Path(options.file)

    try:
        if Path(movie_path).is_file():
            segments_filepath = movie_path.with_suffix(f'{movie_path.suffix}.segments')

            detectors_result = run_segment_detectors(movie_path)
            segments_filepath.write_text(yaml.dump(detectors_result), encoding='utf-8')
        else:
            raise ValueError('Expect file, receive dir')
    except Exception as e:
        logger.exception(e)
