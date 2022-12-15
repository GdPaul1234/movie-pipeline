import logging
from pathlib import Path
import json

from lib.ffmpeg_detect_filter import AudioCrossCorrelationDetect, BlackDetect, SilenceDetect
from util import seconds_to_position

logger = logging.getLogger(__name__)


def run_segment_detectors(movie_path: Path):
    detectors = {
        # 'black': BlackDetect,
        # 'silence': SilenceDetect,
        'axcorrelate_silence': AudioCrossCorrelationDetect
    }
    detected_segments = {}

    for detector_key, detector_value in detectors.items():
        logger.info('Running %s detection...', detector_key)

        detector_instance = detector_value(movie_path)
        detector_result = detector_instance.detect()
        detected_segments[detector_key] = {
            "segments": detector_result,
            "humanized_segments": ','.join([
                '-'.join(map(seconds_to_position, [float(segment['start']), float(segment['end'])]))
                for segment in detector_result
            ])
        }

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
