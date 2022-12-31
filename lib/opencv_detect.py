from dataclasses import dataclass
import logging
from abc import ABC
from pathlib import Path
from typing import Any, cast
from rich.progress import Progress, TaskID
from deffcode import Sourcer
import cv2

from configparser import ConfigParser
from lib.ffmpeg_with_progress import ffmpeg_frame_producer
from lib.opencv_annotator import draw_detection_box
from lib.title_extractor import load_metadata
from lib.ui_factory import transient_task_progress
from models.detected_segments import DetectedSegment
from util import timed_run

logger = logging.getLogger(__name__)

segments_min_gap = 20.
segments_min_duration = 120.
threshold = 0.8


@dataclass
class PositionMetadata:
    position_in_s: float
    duration: float
    target_fps: float


@dataclass
class ProgressTask:
    progress: Progress
    task_id: TaskID


def OpenCVDetectWithInjectedTemplate(detector: type['OpenCVBaseDetect'], movie_path: Path, config):
    templates_path = Path(config.get('SegmentDetection', 'templates_path'))

    metadata = load_metadata(movie_path)

    if metadata is None:
        raise ValueError('No metadata found. Please retry when the movie is finished')

    template_path = templates_path.joinpath(f"{metadata['channel']}.bmp")

    if not templates_path.exists():
        raise FileNotFoundError(template_path)

    return lambda m: detector(m, template_path)


class OpenCVBaseDetect(ABC):
    def __init__(self, video_path: Path, template_path: Path) -> None:
        self._video_path = video_path
        self._template_path = template_path

        self._segments = []

    def _update_segments(self, position: float):
        position = round(position, 2)

        if len(self._segments) == 0 or (position - self._segments[-1]['end']) > segments_min_gap:
            self._segments = [segment for segment in self._segments if segment['duration'] > segments_min_duration]
            self._segments.append({'start': position, 'end': position, 'duration': 0})
        else:
            self._segments[-1]['end'] = position
            self._segments[-1]['duration'] = round(position - self._segments[-1]['start'], 2)

    def _build_crop_filter(self):
        template_metadata_path = self._template_path.with_suffix('.ini')

        if not template_metadata_path.exists():
            return ''

        config = ConfigParser()
        config.read(template_metadata_path)

        template_metadata = config['General']

        w = template_metadata.getint('x2') - template_metadata.getint('x1')
        h = template_metadata.getint('y2') - template_metadata.getint('y1')
        x, y = template_metadata.getint('x1'), template_metadata.getint('y1')

        return f'crop={w=}:{h=}:{x=}:{y=}'

    def _do_detect(
        self,
        image: cv2.Mat,
        template: cv2.Mat,
        position_metadata: PositionMetadata,
        progress_task: ProgressTask,
        result_window_name: str
    ) -> bool:
        ...

    def detect(self) -> list[DetectedSegment]:
        template = cv2.imread(str(self._template_path), cv2.IMREAD_GRAYSCALE)

        sourcer = Sourcer(str(self._video_path)).probe_stream()
        video_metadata = cast(dict[str, Any], sourcer.retrieve_metadata())

        target_fps = 5
        duration = video_metadata['source_duration_sec']
        result_window_name = f'Match Template Result - {self._video_path}'

        if logger.isEnabledFor(logging.DEBUG):
            cv2.namedWindow(result_window_name, cv2.WINDOW_NORMAL)

        with Progress() as progress:
            try:
                with transient_task_progress(progress, description='match_template', total=duration) as task_id:
                    for frame, _, position_in_s in ffmpeg_frame_producer(
                        self._video_path, target_fps=target_fps,
                        other_video_filter=self._build_crop_filter()
                    ):
                        image = frame.copy()
                        if self._do_detect(
                            image,
                            template,
                            PositionMetadata(position_in_s, duration, target_fps),
                            ProgressTask(progress, task_id),
                            result_window_name
                        ):
                            break
            finally:
                cv2.destroyAllWindows()

        logger.debug('Segments before final cleaning: %s', '\n'.join(map(str, self._segments)))
        return self._segments


class OpenCVTemplateDetect(OpenCVBaseDetect):
    def _do_detect(
        self,
        image: cv2.Mat,
        template: cv2.Mat,
        position_metadata: PositionMetadata,
        progress_task: ProgressTask,
        result_window_name: str
    ) -> bool:
        def match_template(image):
            return cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)

        result, process_time = timed_run(match_template, image)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        progress_task.progress.update(progress_task.task_id, completed=position_metadata.position_in_s)

        if max_val >= threshold:
            self._update_segments(position_metadata.position_in_s)

        if logger.isEnabledFor(logging.DEBUG):
            image_shape = template.shape[::-1]
            match_result = (max_val, max_loc)
            stats = {
                "fps": round(process_time and position_metadata.target_fps / process_time),
                "position": position_metadata.position_in_s,
                "duration": position_metadata.duration,
                "segments": self._segments
            }

            if draw_detection_box(result_window_name, image, image_shape, match_result, threshold, stats):
                return True

        return False
