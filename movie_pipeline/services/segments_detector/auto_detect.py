import logging
from functools import partial
from pathlib import Path
from typing import Generator

from ...lib.ffmpeg.ffmpeg_detect_filter import CropDetect
from ...lib.opencv.opencv_detect import OpenCVDetectWithInjectedTemplate, OpenCVTemplateDetect
from ...models.detected_segments import DetectedSegment
from ...settings import Settings
from .core import BaseDetect, DummyDetect, SegmentDetector

logger = logging.getLogger(__name__)


AVAILABLE_REGISTERED_SEGMENT_DETECTOR: dict[str, SegmentDetector] = {
    'match_template': partial(OpenCVDetectWithInjectedTemplate, OpenCVTemplateDetect),
    'crop': CropDetect,
    'dummy': DummyDetect
}


class NoSuitableSegmentDetectorFound(Exception):
    pass


class AutoDetect(BaseDetect):
    def __init__(self, movie_path: Path, config: Settings) -> None:
        for registered_segment_detector_name, registered_segment_detector_value in AVAILABLE_REGISTERED_SEGMENT_DETECTOR.items():
            try:
                if (detector := registered_segment_detector_value(movie_path, config)).should_proceed():
                    self._detector = detector
                    return
            except Exception as e:
                logger.info(f'Skip {registered_segment_detector_name}: {e}')
                continue

        raise NoSuitableSegmentDetectorFound(f'No suitable segment detector found for "{str(movie_path)}"')

    def should_proceed(self) -> bool:
        return False

    def detect_with_progress(self) -> Generator[float, None, list[DetectedSegment]]:
        detect_progress = self._detector.detect_with_progress()

        try:
            while True:
                yield next(detect_progress)
        except StopIteration as e:
            return e.value 
