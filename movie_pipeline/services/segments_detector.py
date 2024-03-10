import json
import logging
from pathlib import Path
from typing import cast

from ..lib.ffmpeg.ffmpeg_detect_filter import AudioCrossCorrelationDetect, CropDetect
from ..lib.opencv.opencv_detect import OpenCVDetectWithInjectedTemplate, OpenCVTemplateDetect
from ..models.detected_segments import DetectedSegment, humanize_segments, merge_adjacent_segments
from ..settings import Settings

logger = logging.getLogger(__name__)


def run_segment_detectors(movie_path: Path, selected_detectors_key, config: Settings):
    detected_segments = {}

    def try_match_template(movie_path):
        try:
            return OpenCVDetectWithInjectedTemplate(OpenCVTemplateDetect, movie_path, config)(movie_path)
        except Exception as e:
            logger.exception(e)

    try:
        detectors = {
            'axcorrelate_silence': AudioCrossCorrelationDetect,
            'match_template': try_match_template,
            'crop': CropDetect
        }

        selected_detectors = { key: detectors[key] for key in selected_detectors_key }

        for detector_key, detector_value in selected_detectors.items():
            logger.info('Running %s detection...', detector_key)

            detector_instance = detector_value(movie_path)
            detector_result = cast(list[DetectedSegment], detector_instance.detect())
            detector_result = merge_adjacent_segments(detector_result)
            detected_segments[detector_key] = humanize_segments(detector_result)

    except Exception as e:
        logger.exception(e)
        logger.warning('Skipping " %s"', movie_path)

    return detected_segments


def dump_segments_to_file(detectors_result, movie_path: Path):
    if detectors_result == {}:
        return

    segments_filepath = movie_path.with_suffix(f'{movie_path.suffix}.segments.json')
    segments_filepath.write_text(json.dumps(detectors_result, indent=2), encoding='utf-8')
