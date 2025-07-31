import logging
import math
import multiprocessing
import re
from itertools import pairwise
from pathlib import Path
from typing import Any, Generator, Literal, Optional, cast

import ffmpeg
from deffcode import Sourcer

from ...lib.ffmpeg.ffmpeg_cli_presets import get_ffprefixes
from ...lib.util import position_in_seconds
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

        self._segments_min_gap = config.SegmentDetection.segments_min_gap
        self._segments_min_duration = config.SegmentDetection.segments_min_duration
        self._config = config

        sourcer = Sourcer(str(movie_path), custom_ffmpeg=str(config.ffmpeg_path)).probe_stream()
        video_metadata = cast(dict[str, Any], sourcer.retrieve_metadata())
        self._duration: float = video_metadata['source_duration_sec']
        self._nframes: int = video_metadata['approx_video_nframes']
        self._framerate: float = video_metadata['source_video_framerate']

    def _map_out(self, output: list[str], no_post_processing=False) -> list[DetectedSegment]:
        raw_segments = [
            DetectedSegment(**{key.split('_')[1]: float(value) for key, value in self.filter_pattern.findall(line)})
            for line in output or []
        ]

        if no_post_processing or len(raw_segments) < 2:
            return raw_segments

        pairs = list(pairwise(segment for segment in raw_segments if segment['duration'] > self._segments_min_duration))

        segments = [
            current_segment
            if next_segment['start'] - current_segment['end'] > self._segments_min_gap
            else DetectedSegment(start=current_segment['start'], end=next_segment['end'], duration=next_segment['end'] - current_segment['start'])
            for current_segment, next_segment in pairs
        ]

        segments.append(pairs[-1][1])

        return segments

    def _build_command(self, in_file_path: Path, target_fps: float):
        in_file = ffmpeg.input(str(in_file_path))

        command = getattr(in_file, self.media)

        if self.media == 'video':
            command = command.filter_('fps', target_fps)

        command = command.filter_(self.detect_filter, **self.args)

        return command.output('-', format='null')

    def should_proceed(self) -> bool:
        logger.info(f'Checking if should proceed "{str(self._movie_path)}" with {self.__class__.__name__}...')

        if self.media == 'audio':
            return True

        target_nframes = 10
        proceed_thresold = 0.55
        all_segments: list[DetectedSegment] = []

        for frame_position in range(0, self._nframes, self._nframes // target_nframes):
            position = frame_position / self._framerate
            detector = self.__class__(self._movie_path, self._config)
            detect_progress = detector.detect_with_progress(seek_ss=position, seek_t=1, no_post_processing=True)

            try:
                while True:
                    next(detect_progress)
            except StopIteration as e:
                [all_segments.append(segment) for index, segment in enumerate(e.value) if index < 1]

        return len(all_segments) > proceed_thresold * target_nframes

    def detect_with_progress(
        self,
        target_fps=5.0,
        seek_ss: Optional[str | float] = None,
        seek_t: Optional[str | float] = None,
        no_post_processing=False
    ) -> Generator[float, None, list[DetectedSegment]]:
        command = self._build_command(self._movie_path, target_fps)

        cmd = [
            'ffmpeg',
            *get_ffprefixes(self._config.ffmpeg_hwaccel),
            *(['-ss', str(seek_ss)] if seek_ss is not None else []),
            *(['-t', str(seek_t)] if seek_t is not None else [])
        ]

        if not no_post_processing:
            logger.info('Running: %s with %s', command.compile(), cmd)

        detection_result = []

        stop_signal = multiprocessing.Event()

        process = ffmpeg_command_with_progress(
            command,
            cmd=cmd,
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
            detection_result = self._map_out(e.value, no_post_processing)
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

    def _map_out(self, output: list[str], no_post_processing=False):
        grouped_output = zip(*[iter(output)]*2)
        flattened_ouput = [f'{start} {end}' for start, end in grouped_output]
        return super()._map_out(flattened_ouput, no_post_processing)


class FFmpegCropSegmentMergerContainer(FFmpegLineContainer):
    # see https://fr.wikipedia.org/wiki/Format_d'image
    whitelisted_ratios = [1.33, 1.37, 1.56, 1.66, 1.85, 2., 2.20, 2.35, 2.39, 2.55, 2.76]

    def __init__(self, filter_pattern, config: Settings) -> None:
        super().__init__()
        self._filter_pattern = filter_pattern
        self._found_ratios: set[float] = set()

        self._segments_min_gap = config.SegmentDetection.segments_min_gap
        self._segments_min_duration = config.SegmentDetection.segments_min_duration

        self._segments: list[DetectedSegment] = []

    @property
    def segments(self):
        return [segment for segment in self._segments if segment['duration'] > self._segments_min_duration]

    def append(self, line: str):
        mapped_line = dict(self._filter_pattern.findall(line))
        position = float(mapped_line['t'])
        ratio = float(mapped_line['w']) / (float(mapped_line['h']) or 1)

        self._found_ratios.add(ratio)

        if not any(math.isclose(whitelisted, ratio, rel_tol=1e-02) for whitelisted in self.whitelisted_ratios):
            return

        last_segment = self._segments[-1] if len(self._segments) > 0 else None

        if last_segment is None or (position - last_segment['end']) > self._segments_min_gap:
            self._segments.append({'start': position, 'end': position, 'duration': 0})
        else:
            last_segment['end'] = position
            last_segment['duration'] = round(position - last_segment['start'], 2)


class CropDetect(BaseFFmpegFilterDetect):
    detect_filter = 'cropdetect'
    media = 'video'
    filter_pattern = re.compile(r' (x1|x2|y1|y2|w|h|x|y|pts|t)\s*\:\s*(\S+)')
    args = {'reset_count': 3} # cf https://ffmpeg.org/ffmpeg-filters.html#toc-cropdetect

    def __init__(self, movie_path: Path, config: Settings) -> None:
        super().__init__(movie_path, config)
        self.line_container = FFmpegCropSegmentMergerContainer(self.filter_pattern, config)

    def _map_out(self, output: list[str], no_post_processing=False) -> list[DetectedSegment]:
        logger.info(f'found_ratios: {sorted(self.line_container._found_ratios)}')
        return self.line_container.segments if not no_post_processing else self.line_container._segments
