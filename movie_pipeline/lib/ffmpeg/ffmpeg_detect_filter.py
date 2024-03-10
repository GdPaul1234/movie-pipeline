import logging
import math
from typing import Literal
from pathlib import Path
from abc import ABC
from rich.progress import Progress
import multiprocessing
import re
import ffmpeg

from .ffmpeg_with_progress import FFmpegLineContainer, FFmpegLineFilter, ffmpeg_command_with_progress
from ...lib.ui_factory import transient_task_progress
from ...lib.util import position_in_seconds, total_movie_duration


logger = logging.getLogger(__name__)

class BaseDetect(ABC):
    detect_filter: str
    media: Literal['audio', 'video']
    filter_pattern = re.compile('')
    line_container = FFmpegLineContainer()
    args = {}

    def __init__(self, movie_path: Path) -> None:
        self._movie_path = movie_path

    def _map_out(self, output: list[str]):
        return [{key.split('_')[1]: float(value)
                 for key, value in self.filter_pattern.findall(line)}
                for line in output or []]

    def _build_command(self, in_file_path: Path):
        in_file = ffmpeg.input(str(in_file_path))
        command = getattr(in_file, self.media).filter_(self.detect_filter, **self.args)

        if self.media == 'video':
            command = command.filter_('fps', 5)

        return command.output('-', format='null')

    def detect(self):
        total_duration = total_movie_duration(self._movie_path)

        command = self._build_command(self._movie_path)

        logger.info('Running: %s', command.compile())
        detection_result = []

        with Progress() as progress:
            with transient_task_progress(progress, description=self.detect_filter, total=total_duration) as task_id:
                stop_signal = multiprocessing.Event()

                process = ffmpeg_command_with_progress(
                    command,
                    cmd=['ffmpeg', '-hwaccel', 'cuda'],
                    keep_log=True,
                    line_filter=FFmpegLineFilter(self.filter_pattern),
                    line_container=self.line_container,
                    stop_signal=stop_signal
                )

                try:
                    while True:
                        try:
                            if (item := next(process)).get('time'):
                                processed_time = position_in_seconds(item['time'])
                                progress.update(task_id, completed=processed_time)

                        except KeyboardInterrupt:
                            stop_signal.set()

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
        audio_tracks_input = input('Enter audio tracks to correlate separated with space: (0..nb_tracks, max: 2) ')
        audio_tracks = map(int, audio_tracks_input.split(' ', 2))

        in_files = [ffmpeg.input(str(in_file_path))[f'a:{i}'] for i in audio_tracks]

        return (
            ffmpeg
            .filter_(in_files, 'axcorrelate')
            .filter_('silencedetect', noise='0dB', duration=420)
            .output('-', f='null')
        )


class FFmpegCropSegmentMergerContainer(FFmpegLineContainer):
    # see https://fr.wikipedia.org/wiki/Format_d'image
    whitelisted_ratios = [1.33, 1.37, 2.39, 2.20, 1.66, 2.]

    def __init__(self, filter_pattern) -> None:
        super().__init__()
        self._filter_pattern = filter_pattern

    def lines(self):
        def mapper(line):
            return '\t'.join(f'{key} : {line[key]}' for key in line.keys())

        return list(map(mapper, self._lines))

    def append(self, line: str):
        mapped_line = {key: value for key, value in self._filter_pattern.findall(line)}
        position = float(mapped_line[' t'])

        w, h = tuple(map(float, (mapped_line['w'], mapped_line['h'])))
        if not any(map(lambda x: math.isclose(x, w/h, rel_tol=1e-02), self.whitelisted_ratios)):
            return

        def add_segment():
            self._lines.append(mapped_line | new_segment)
            logger.info(mapped_line | new_segment)

        new_segment = { 'start': position, 'end': position, 'duration': 0 }
        if len(self._lines) == 0:
            add_segment()
            return

        last_segment = self._lines[-1]

        if (position - last_segment['end']) > 0.1:
            add_segment()
        else:
            last_segment['end'] = position
            last_segment['duration'] = round(position - last_segment['start'], 2)


class CropDetect(BaseDetect):
    detect_filter = 'cropdetect'
    media = 'video'
    filter_pattern = re.compile(r'(x1|x2|y1|y2|w|h|x|y|pts| t)\s*\:\s*(\S+)')
    line_container = FFmpegCropSegmentMergerContainer(filter_pattern)
