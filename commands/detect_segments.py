import logging
from pathlib import Path
from typing import cast
import json

from lib.ffmpeg_detect_filter import AudioCrossCorrelationDetect, CropDetect
from lib.opencv_detect import OpenCVDetectWithInjectedTemplate, OpenCVTemplateDetect
from models.detected_segments import DetectedSegment, humanize_segments, merge_adjacent_segments

logger = logging.getLogger(__name__)


def run_segment_detectors(movie_path: Path, config):
    detected_segments = {}

    try:
        detectors = {
            # 'axcorrelate_silence': AudioCrossCorrelationDetect,
            'match_template': OpenCVDetectWithInjectedTemplate(OpenCVTemplateDetect, movie_path, config),
            # 'crop': CropDetect
        }

        for detector_key, detector_value in detectors.items():
            logger.info('Running %s detection...', detector_key)

            detector_instance = detector_value(movie_path)
            detector_result = cast(list[DetectedSegment], detector_instance.detect())
            detector_result = merge_adjacent_segments(detector_result)
            detected_segments[detector_key] = humanize_segments(detector_result)
    except Exception as e:
        logger.error(e)
        logger.warning('Skipping " %s"', movie_path)

    return detected_segments


def dump_segments_to_file(detectors_result, movie_path: Path):
    if detectors_result == {}:
        return

    segments_filepath = movie_path.with_suffix(f'{movie_path.suffix}.segments.json')
    segments_filepath.write_text(json.dumps(detectors_result, indent=2), encoding='utf-8')


def command(options, config):
    logger.debug('args: %s', vars(options))
    filepath = Path(options.file)

    try:
        if filepath.is_file():
            detectors_result = run_segment_detectors(filepath, config)
            dump_segments_to_file(detectors_result, movie_path=filepath)
        elif filepath.is_dir():
            for metadata_path in filepath.glob('*.metadata.json'):
                movie_path = metadata_path.with_name(f"{metadata_path.name.removesuffix('.metadata.json')}")
                logger.info('Search segments in "%s"...', movie_path)

                if not movie_path.with_suffix(f'{movie_path.suffix}.segments.json').exists():
                    detectors_result = run_segment_detectors(movie_path, config)
                    dump_segments_to_file(detectors_result, movie_path)
                else:
                    logger.warning('Segments already exist, skipping "%s"', movie_path)
        else:
            raise ValueError('File is not a movie')
    except Exception as e:
        logger.exception(e)
