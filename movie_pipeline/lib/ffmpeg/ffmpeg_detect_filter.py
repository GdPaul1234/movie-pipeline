import logging
import math
import multiprocessing
import re
from abc import ABC
from pathlib import Path
from typing import Generator, Literal

import ffmpeg
from rich.progress import Progress

from ...lib.ffmpeg.ffmpeg_cli_presets import get_ffprefixes
from ...lib.util import position_in_seconds, total_movie_duration
from ...models.detected_segments import DetectedSegment
from ...settings import Settings
from ..ui_factory import transient_task_progress
from .ffmpeg_with_progress import FFmpegLineContainer, FFmpegLineFilter, ffmpeg_command_with_progress

logger = logging.getLogger(__name__)

class BaseDetect(ABC):
    detect_filter: str
    media: Literal['audio', 'video']
    filter_pattern = re.compile('')
    args = {}

    def __init__(self, movie_path: Path, config: Settings) -> None:
        self.line_container = FFmpegLineContainer()
        self._movie_path = movie_path
        self._config = config

    def _map_out(self, output: list[str]) -> list[DetectedSegment]:
        return [
            DetectedSegment(**{key.split('_')[1]: float(value) for key, value in self.filter_pattern.findall(line)})
            for line in output or []
        ]

    def _build_command(self, in_file_path: Path):
        in_file = ffmpeg.input(str(in_file_path))
        command = getattr(in_file, self.media).filter_(self.detect_filter, **self.args)

        if self.media == 'video':
            command = command.filter_('fps', 5)

        return command.output('-', format='null')

    def detect_with_progress(self) -> Generator[float, None, list[DetectedSegment]]:
        total_duration = total_movie_duration(self._movie_path)

        command = self._build_command(self._movie_path)

        logger.info('Running: %s', command.compile())
        detection_result = []

        stop_signal = multiprocessing.Event()

        process = ffmpeg_command_with_progress(
            command,
            cmd=['ffmpeg', *get_ffprefixes(self._config.ffmpeg_hwaccel)],
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
                        yield processed_time / total_duration
                except KeyboardInterrupt:
                    stop_signal.set()

        except StopIteration as e:
            detection_result = self._map_out(e.value)
            logger.info(detection_result)
            return detection_result

    def detect(self) -> list[DetectedSegment]:
        detect_progress = self.detect_with_progress()

        with Progress() as progress:
            with transient_task_progress(progress, description=self.detect_filter, total=1.0) as task_id:
                try:
                    while True:
                        progress_percent = next(detect_progress)
                        progress.update(task_id, completed=progress_percent)
                except StopIteration as e:
                    return e.value


class AudioCrossCorrelationDetect(BaseDetect):
    detect_filter = 'axcorrelate'
    media = 'audio'
    filter_pattern = re.compile(r'(silence_start|silence_end|silence_duration)\s*\:\s*(\S+)')

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
    
    def _map_out(self, output: list[str]):
        grouped_output = zip(*[iter(output)]*2)
        flattened_ouput = [f'{start} {end}' for start, end in grouped_output] # type: ignore
        return super()._map_out(flattened_ouput)


class FFmpegCropSegmentMergerContainer(FFmpegLineContainer):
    # see https://fr.wikipedia.org/wiki/Format_d'image
    whitelisted_ratios = [1.33, 1.37, 1.56, 1.66, 1.85, 2., 2.20, 2.35, 2.39, 2.55, 2.76]

    def __init__(self, filter_pattern) -> None:
        super().__init__()
        self._filter_pattern = filter_pattern
        self._found_ratios: set[float] = set()
        self.segments: list[DetectedSegment] = []

    def append(self, line: str):
        mapped_line = {key: value for key, value in self._filter_pattern.findall(line)}
        position = float(mapped_line['t'])
        ratio = float(mapped_line['w']) / float(mapped_line['h'])

        self._found_ratios.add(ratio)

        if not any(math.isclose(whitelisted, ratio, rel_tol=1e-02) for whitelisted in self.whitelisted_ratios):
            return

        last_segment = self.segments[-1] if len(self.segments) > 0 else None

        if last_segment is None or (position - last_segment['end']) > 0.1:
            self.segments.append({ 'start': position, 'end': position, 'duration': 0 })
        else:
            last_segment['end'] = position
            last_segment['duration'] = round(position - last_segment['start'], 2)


class CropDetect(BaseDetect):
    detect_filter = 'cropdetect'
    media = 'video'
    filter_pattern = re.compile(r' (x1|x2|y1|y2|w|h|x|y|pts|t)\s*\:\s*(\S+)')
    args={'reset_count': 3} # cf https://ffmpeg.org/ffmpeg-filters.html#toc-cropdetect

    def __init__(self, movie_path: Path, config: Settings) -> None:
        super().__init__(movie_path, config)
        self.line_container = FFmpegCropSegmentMergerContainer(self.filter_pattern)

    def _map_out(self, output: list[str]) -> list[DetectedSegment]:
        logger.info(f'found_ratios: {sorted(self.line_container._found_ratios)}')
        return self.line_container.segments
