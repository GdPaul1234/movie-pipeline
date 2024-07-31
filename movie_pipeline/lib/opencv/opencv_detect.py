import json
import logging
from abc import ABC
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator, cast

import cv2
from deffcode import Sourcer
from rich.progress import Progress

from ...lib.ffmpeg.ffmpeg_with_progress import ffmpeg_frame_producer
from ..ui_factory import transient_task_progress
from ...lib.util import timed_run
from ...models.detected_segments import DetectedSegment
from ...settings import Settings
from .opencv_annotator import draw_detection_box

logger = logging.getLogger(__name__)

@dataclass
class PositionMetadata:
    position_in_s: float
    duration: float
    target_fps: float


@dataclass
class RealTimeDetectResult:
    value: float
    location: cv2.typing.Point


def load_metadata(movie_path: Path):
    movie_metadata_path = movie_path.with_suffix(f'{movie_path.suffix}.metadata.json')

    if movie_metadata_path.exists():
        return json.loads(movie_metadata_path.read_text(encoding='utf-8'))


def OpenCVDetectWithInjectedTemplate(detector: type['OpenCVBaseDetect'], movie_path: Path, config: Settings):
    if config.SegmentDetection is None:
        raise ValueError('No config path provided')

    templates_path = config.SegmentDetection.templates_path
    metadata = load_metadata(movie_path)

    if metadata is None:
        raise ValueError('No metadata found. Please retry when the movie is finished')

    template_path = templates_path.joinpath(f"{metadata['channel']}.bmp")

    if not template_path.exists():
        raise FileNotFoundError(template_path)

    return detector(movie_path, template_path, config)


def get_template_metadata(template_path: Path):
    template_metadata_path = template_path.with_suffix('.ini')

    if not template_metadata_path.exists():
        logger.warning('Cannot found template metadata, cropping disabled')
        return None

    config = ConfigParser()
    config.read(template_metadata_path)

    return config['General']


def build_crop_filter(template_path: Path):
    template_metadata = get_template_metadata(template_path)

    if template_metadata is None:
        return ''

    w = template_metadata.getint('x2') - template_metadata.getint('x1')
    h = template_metadata.getint('y2') - template_metadata.getint('y1')
    x, y = template_metadata.getint('x1'), template_metadata.getint('y1')

    return f'crop={w=}:{h=}:{x=}:{y=}'


class OpenCVBaseDetect(ABC):
    other_video_filter = ''

    def __init__(self, video_path: Path, template_path: Path, config: Settings) -> None:
        self._video_path = video_path
        self._template_path = template_path

        if config.SegmentDetection is None:
            raise ValueError('SegmentDetection settings is missing in provided config')

        self._segments_min_gap = config.SegmentDetection.segments_min_gap
        self._segments_min_duration = config.SegmentDetection.segments_min_duration
        self._threshold = config.SegmentDetection.match_template_threshold
        self._config = config

        sourcer = Sourcer(str(video_path), custom_ffmpeg=str(config.ffmpeg_path)).probe_stream()
        video_metadata = cast(dict[str, Any], sourcer.retrieve_metadata())
        self._duration: float = video_metadata['source_duration_sec']

        self._segments: list[DetectedSegment] = []

    def _update_segments(self, position: float):
        position = round(position, 2)

        if len(self._segments) == 0 or (position - self._segments[-1]['end']) > self._segments_min_gap:
            self._segments = [segment for segment in self._segments if segment['duration'] > self._segments_min_duration]
            self._segments.append({'start': position, 'end': position, 'duration': 0})
        else:
            self._segments[-1]['end'] = position
            self._segments[-1]['duration'] = round(position - self._segments[-1]['start'], 2)

    def _do_detect(
        self,
        image: cv2.typing.MatLike,
        template: cv2.typing.MatLike,
        position_metadata: PositionMetadata,
        result_window_name: str
    ) -> tuple[float, bool]:
        ...

    def _show_detect_result(
        self,
        image: cv2.typing.MatLike,
        template: cv2.typing.MatLike,
        position_metadata: PositionMetadata,
        result: RealTimeDetectResult,
        process_time: float,
        result_window_name: str
    ):
        image_shape = cast(tuple[int, int], template.shape[::-1])
        match_result = (result.value, result.location)
        stats = {
            "fps": round(process_time and position_metadata.target_fps / process_time),
            "position": position_metadata.position_in_s,
            "duration": position_metadata.duration,
            "segments": self._segments
        }

        return draw_detection_box(result_window_name, image, image_shape, match_result, self._threshold, stats)

    def detect_with_progress(self) -> Generator[float, None, list[DetectedSegment]]:
        template = cv2.imread(str(self._template_path), cv2.IMREAD_GRAYSCALE)

        target_fps = 5

        result_window_name = f'Match Template Result - {self._video_path}'

        if logger.isEnabledFor(logging.DEBUG):
            cv2.namedWindow(result_window_name, cv2.WINDOW_NORMAL)

        try:
            for frame, _, position_in_s in ffmpeg_frame_producer(
                self._video_path, target_fps=target_fps,
                other_video_filter=self.other_video_filter,
                config=self._config
            ):
                image = frame.copy()
                progress_percent, should_exit = self._do_detect(
                    image,
                    template,
                    PositionMetadata(position_in_s, self._duration, target_fps),
                    result_window_name
                )
                yield progress_percent

                if should_exit:
                    break
        finally:
            cv2.destroyAllWindows()

        logger.debug('Segments before final cleaning: %s', '\n'.join(map(str, self._segments)))
        return self._segments


    def detect(self) -> list[DetectedSegment]:
        detect_progress = self.detect_with_progress()

        with Progress() as progress:
            with transient_task_progress(progress, description='match_template', total=1.0) as task_id:
                try:
                    while True:
                        progress_percent = next(detect_progress)
                        progress.update(task_id, completed=progress_percent)
                except StopIteration as e:
                    return e.value


class OpenCVTemplateDetect(OpenCVBaseDetect):
    def __init__(self, video_path: Path, template_path: Path, config: Settings) -> None:
        super().__init__(video_path, template_path, config)
        self.other_video_filter = build_crop_filter(template_path)

    def _do_detect(
        self,
        image: cv2.typing.MatLike,
        template: cv2.typing.MatLike,
        position_metadata: PositionMetadata,
        result_window_name: str
    ) -> tuple[float, bool]:
        def match_template(image):
            return cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)

        result, process_time = timed_run(match_template, image)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        progress_percent = position_metadata.position_in_s / self._duration

        if max_val >= self._threshold:
            self._update_segments(position_metadata.position_in_s)

        if logger.isEnabledFor(logging.DEBUG):
            return progress_percent, self._show_detect_result(
                image,
                template,
                position_metadata,
                RealTimeDetectResult(max_val, max_loc),
                process_time,
                result_window_name
            )

        return progress_percent, False
