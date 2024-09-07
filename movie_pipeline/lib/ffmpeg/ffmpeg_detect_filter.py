import logging
import math
import multiprocessing
import re
from itertools import pairwise
from pathlib import Path
from typing import Generator, Literal

import ffmpeg

from ...lib.ffmpeg.ffmpeg_cli_presets import get_ffprefixes
from ...lib.util import position_in_seconds, total_movie_duration
from ...models.detected_segments import DetectedSegment
from ...services.segments_detector.core import BaseDetect
from ...settings import Settings
from .ffmpeg_with_progress import FFmpegLineContainer, FFmpegLineFilter, ffmpeg_command_with_progress

logger = logging.getLogger(__name__)

class BaseFFmpegFilterDetect(BaseDetect):
    detect_filter: str
    media: Literal['audio', 'video']
    filter_pattern = re.compile('')
    args = {}

    def __init__(self, movie_path: Path, config: Settings) -> None:
        self.line_container = FFmpegLineContainer()
        self._movie_path = movie_path

        if config.SegmentDetection is None:
            raise ValueError('SegmentDetection settings is missing in provided config')

        self._segments_min_gap = config.SegmentDetection.segments_min_gap
        self._segments_min_duration = config.SegmentDetection.segments_min_duration
        self._config = config

        self._duration = total_movie_duration(self._movie_path)

    def _map_out(self, output: list[str]) -> list[DetectedSegment]:
        pairs = list(pairwise(
            segment
            for line in output or []
            if (segment := DetectedSegment(**{key.split('_')[1]: float(value) for key, value in self.filter_pattern.findall(line)}))
            and segment['duration'] > self._segments_min_duration
        ))

        segments = [
            current_segment 
            for current_segment, next_segment in pairs
            if next_segment['start'] - current_segment['end'] > self._segments_min_gap
        ]

        if len(pairs) > 0:
            segments.append(pairs[-1][1])

        return segments

    def _build_command(self, in_file_path: Path, target_fps=5.0):
        in_file = ffmpeg.input(str(in_file_path))

        command = getattr(in_file, self.media)

        if self.media == 'video':
            command = command.filter_('fps', target_fps)

        command = command.filter_(self.detect_filter, **self.args)

        return command.output('-', format='null')
    
    def should_proceed(self) -> bool:
        if self.media == 'audio':
            return True

        target_nframes = 100.0
        detect_progress = self.detect_with_progress(target_fps=target_nframes / self._duration)

        try:
            while True:
                next(detect_progress)
        except StopIteration as e:
            return len(e.value) > 0 if isinstance(e.value, list) else False

    def detect_with_progress(self, target_fps=5.0) -> Generator[float, None, list[DetectedSegment]]:
        command = self._build_command(self._movie_path, target_fps)

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
                        yield processed_time / self._duration
                except KeyboardInterrupt:
                    stop_signal.set()

        except StopIteration as e:
            detection_result = self._map_out(e.value)
            logger.info(detection_result)
            return detection_result


class AudioCrossCorrelationDetect(BaseFFmpegFilterDetect):
    detect_filter = 'axcorrelate'
    media = 'audio'
    filter_pattern = re.compile(r'(silence_start|silence_end|silence_duration)\s*\:\s*(\S+)')

    def _build_command(self, in_file_path: Path, _):
        audio_tracks = [
            index
            for index, stream in enumerate(ffmpeg.probe(in_file_path, select_streams='a')['streams']) 
            if sum(stream['disposition'][field] for field in ('visual_impaired', 'descriptions')) < 1
        ]

        if len(audio_tracks) < 2:
            raise ValueError('Expect to have at least 2 audio tracks (without counting impaired / descriptions audio)')

        in_files = [ffmpeg.input(str(in_file_path))[f'a:{i}'] for index, i in enumerate(audio_tracks) if index < 2]

        return (
            ffmpeg
            .filter_(in_files, 'axcorrelate')
            .filter_('silencedetect', noise='0dB', duration=2)
            .output('-', f='null')
        )
    
    def _map_out(self, output: list[str]):
        grouped_output = zip(*[iter(output)]*2)
        flattened_ouput = [f'{start} {end}' for start, end in grouped_output]
        return super()._map_out(flattened_ouput)


class FFmpegCropSegmentMergerContainer(FFmpegLineContainer):
    # see https://fr.wikipedia.org/wiki/Format_d'image
    whitelisted_ratios = [1.33, 1.37, 1.56, 1.66, 1.85, 2., 2.20, 2.35, 2.39, 2.55, 2.76]

    def __init__(self, filter_pattern, config: Settings) -> None:
        super().__init__()
        self._filter_pattern = filter_pattern
        self._found_ratios: set[float] = set()

        if config.SegmentDetection is None:
            raise ValueError('SegmentDetection settings is missing in provided config')

        self._segments_min_gap = config.SegmentDetection.segments_min_gap
        self._segments_min_duration = config.SegmentDetection.segments_min_duration

        self._segments: list[DetectedSegment] = []

    @property
    def segments(self):
        return [segment for segment in self._segments if segment['duration'] > self._segments_min_duration]

    def append(self, line: str):
        mapped_line = {key: value for key, value in self._filter_pattern.findall(line)}
        position = float(mapped_line['t'])
        ratio = float(mapped_line['w']) / (float(mapped_line['h']) or 1)

        self._found_ratios.add(ratio)

        if not any(math.isclose(whitelisted, ratio, rel_tol=1e-02) for whitelisted in self.whitelisted_ratios):
            return

        last_segment = self._segments[-1] if len(self._segments) > 0 else None

        if last_segment is None or (position - last_segment['end']) > self._segments_min_gap:
            self._segments.append({ 'start': position, 'end': position, 'duration': 0 })
        else:
            last_segment['end'] = position
            last_segment['duration'] = round(position - last_segment['start'], 2)


class CropDetect(BaseFFmpegFilterDetect):
    detect_filter = 'cropdetect'
    media = 'video'
    filter_pattern = re.compile(r' (x1|x2|y1|y2|w|h|x|y|pts|t)\s*\:\s*(\S+)')
    args={'reset_count': 3} # cf https://ffmpeg.org/ffmpeg-filters.html#toc-cropdetect

    def __init__(self, movie_path: Path, config: Settings) -> None:
        super().__init__(movie_path, config)
        self.line_container = FFmpegCropSegmentMergerContainer(self.filter_pattern, config)

    def _map_out(self, output: list[str]) -> list[DetectedSegment]:
        logger.info(f'found_ratios: {sorted(self.line_container._found_ratios)}')
        return self.line_container.segments
