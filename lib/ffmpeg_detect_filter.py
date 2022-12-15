import logging
from typing import Literal
from pathlib import Path
from abc import ABC
from rich.progress import Progress
import re
import ffmpeg

from lib.ffmpeg_with_progress import FFmpegLineFilter, ffmpeg_command_with_progress
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

    def _map_out(self, output: list[str]):
        return [{key.split('_')[1]: value
                 for key, value in self.filter_pattern.findall(line)}
                for line in output]

    def _build_command(self, in_file_path: Path):
        in_file = ffmpeg.input(str(in_file_path))

        return (
            getattr(in_file, self.media)
            .filter_(self.detect_filter, **self.args)
            .output('-', format='null')
        )

    def detect(self):
        total_duration = total_movie_duration(self._movie_path)

        command = self._build_command(self._movie_path)

        logger.info('Running: %s', command.compile())
        detection_result = []

        with Progress() as progress:
             with transient_task_progress(progress, description=self.detect_filter, total=total_duration) as task_id:
                process = ffmpeg_command_with_progress(
                    command,
                    cmd=['ffmpeg', '-hwaccel', 'cuda'],
                    keep_log=True,
                    line_filter=FFmpegLineFilter(self.filter_pattern)
                )

                try:
                    while True:
                        if (item := next(process)).get('time'):
                            processed_time = position_in_seconds(item['time'])
                            progress.update(task_id, completed=processed_time)
                except StopIteration as e:
                    detection_result = self._map_out(e.value)

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


class AudioCrossCorrelationDetect(SilenceDetect):
    detect_filter = 'axcorrelate'

    def _build_command(self, in_file_path: Path):
        # TODO Retrieve that in config
        audio_tracks_input = input('Enter audio tracks to correlate separated with space: (0..nb_tracks, max: 2) ')
        audio_tracks = map(int, audio_tracks_input.split(' ', 2))

        in_files = [ffmpeg.input(str(in_file_path))[f'a:{i}'] for i in audio_tracks]

        return (
            ffmpeg
            .filter_(in_files, 'axcorrelate')
            .filter_('silencedetect', noise='0dB', duration=300)
            .output('-', f='null')
        )
