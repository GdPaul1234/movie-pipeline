import logging
from pathlib import Path
import json

from lib.ffmpeg_detect_filter import BlackDetect, SilenceDetect

logger = logging.getLogger(__name__)


def run_segment_detectors(movie_path: Path):
    detectors = {
        'black': BlackDetect,
        'silence': SilenceDetect
    }
    detected_segments = {}

    for detector_key, detector_value in detectors.items():
        logger.info('Running %s detection...', detector_key)

        detector_instance = detector_value(movie_path)
        detected_segments[detector_key] = detector_instance.detect()

    return detected_segments

def command(options, config):
    logger.debug('args: %s', vars(options))
    movie_path = Path(options.file)

    try:
        if Path(movie_path).is_file():
            segments_filepath = movie_path.with_suffix(f'{movie_path.suffix}.segments.json')

            detectors_result = run_segment_detectors(movie_path)
            segments_filepath.write_text(json.dumps(detectors_result, indent=2), encoding='utf-8')
        else:
            raise ValueError('Expect file, receive dir')
    except Exception as e:
        logger.exception(e)
