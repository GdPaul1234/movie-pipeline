import json
import logging
from enum import Enum
from functools import partial
from pathlib import Path

from rich.progress import Progress

from ...lib.ffmpeg.ffmpeg_detect_filter import AudioCrossCorrelationDetect, CropDetect
from ...lib.opencv.opencv_detect import OpenCVDetectWithInjectedTemplate, OpenCVTemplateDetect
from ...lib.ui_factory import transient_task_progress
from ...models.detected_segments import humanize_segments, merge_adjacent_segments
from ...services.segments_detector.core import DummyDetect
from ...settings import Settings
from .auto_detect import AutoDetect

logger = logging.getLogger(__name__)


class RegisteredSegmentDetector(Enum):
    auto = AutoDetect
    match_template = partial(OpenCVDetectWithInjectedTemplate, OpenCVTemplateDetect)
    crop = CropDetect
    axcorrelate_silence = AudioCrossCorrelationDetect
    dummy = DummyDetect


def run_segment_detectors_with_progress(movie_path: Path, selected_detectors_key, config: Settings, raise_error = False):
    detected_segments = {}

    try:
        selected_detectors = { key: RegisteredSegmentDetector[key].value for key in selected_detectors_key }
        selected_detectors_size = len(selected_detectors)


        for detector_key, detector_value in selected_detectors.items():
            logger.info('Running %s detection...', detector_key)

            detector_instance = detector_value(movie_path, config)
            detect_progress = detector_instance.detect_with_progress()

            try:
                while True:
                    progress_percent = next(detect_progress)
                    yield progress_percent / float(selected_detectors_size)
            except StopIteration as e:
                detected_segments[detector_key] = humanize_segments(merge_adjacent_segments(e.value))

    except Exception as e:
        logger.exception(e)
        logger.warning('Skipping "%s"', movie_path)

        if raise_error:
            raise e

    return detected_segments


def run_segment_detectors(movie_path: Path, selected_detectors_key, config: Settings):
    detect_progress = run_segment_detectors_with_progress(movie_path, selected_detectors_key, config)

    with Progress() as progress:
        with transient_task_progress(progress, description=f'Running {str(movie_path)} segments detection', total=1.0) as task_id:
            try:
                while True:
                    progress_percent = next(detect_progress)
                    progress.update(task_id, completed=progress_percent)
            except StopIteration as e:
                return e.value


def dump_segments_to_file(detectors_result, movie_path: Path):
    if detectors_result == {}:
        return

    segments_filepath = movie_path.with_suffix(f'{movie_path.suffix}.segments.json')
    segments_filepath.write_text(json.dumps(detectors_result, indent=2), encoding='utf-8')
