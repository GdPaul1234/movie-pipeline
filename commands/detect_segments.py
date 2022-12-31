import logging
from pathlib import Path
from typing import cast
import json

from lib.ffmpeg_detect_filter import AudioCrossCorrelationDetect
from lib.opencv_detect import OpenCVDetectWithInjectedTemplate, OpenCVTemplateDetect
from models.detected_segments import DetectedSegment, humanize_segments, merge_adjacent_segments

logger = logging.getLogger(__name__)


def run_segment_detectors(movie_path: Path, config):
    detectors = {
        # 'axcorrelate_silence': AudioCrossCorrelationDetect,
        'match_template': OpenCVDetectWithInjectedTemplate(OpenCVTemplateDetect, movie_path, config)
    }
    detected_segments = {}

    for detector_key, detector_value in detectors.items():
        logger.info('Running %s detection...', detector_key)

        detector_instance = detector_value(movie_path)
        detector_result = cast(list[DetectedSegment], detector_instance.detect())
        detector_result = merge_adjacent_segments(detector_result)
        detected_segments[detector_key] = humanize_segments(detector_result)

    return detected_segments


def command(options, config):
    logger.debug('args: %s', vars(options))
    movie_path = Path(options.file)

    try:
        if Path(movie_path).is_file():
            segments_filepath = movie_path.with_suffix(f'{movie_path.suffix}.segments.json')

            detectors_result = run_segment_detectors(movie_path, config)
            segments_filepath.write_text(json.dumps(detectors_result, indent=2), encoding='utf-8')
        else:
            raise ValueError('Expect file, receive dir')
    except Exception as e:
        logger.exception(e)
