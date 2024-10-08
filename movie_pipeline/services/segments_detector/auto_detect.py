import logging
from enum import Enum
from pathlib import Path
from functools import partial
from typing import Generator

from ...models.detected_segments import DetectedSegment
from ...lib.ffmpeg.ffmpeg_detect_filter import AudioCrossCorrelationDetect, CropDetect
from ...lib.opencv.opencv_detect import OpenCVDetectWithInjectedTemplate, OpenCVTemplateDetect
from ...settings import Settings
from .core import BaseDetect

logger = logging.getLogger(__name__)


class AvailableRegisteredSegmentDetector(Enum):
    match_template = partial(OpenCVDetectWithInjectedTemplate, OpenCVTemplateDetect)
    crop = CropDetect
    axcorrelate_silence = AudioCrossCorrelationDetect


class NoSuitableSegmentDetectorFound(Exception):
    pass


class AutoDetect(BaseDetect):
    def __init__(self, movie_path: Path, config: Settings) -> None:
        for registered_segment_detector in AvailableRegisteredSegmentDetector:
            try:
                if (detector := registered_segment_detector.value(movie_path, config)).should_proceed():
                    self._detector = detector
                    return
            except Exception as e:
                logger.info(f'Skip {registered_segment_detector.name}: {e}')
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
