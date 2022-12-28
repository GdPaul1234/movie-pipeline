import logging
from pathlib import Path
import json
from typing import TypedDict, cast

from lib.ffmpeg_detect_filter import AudioCrossCorrelationDetect, BlackDetect, SilenceDetect
from lib.opencv_detect import OpenCVTemplateDetectWithInjectedTemplate
from util import seconds_to_position

logger = logging.getLogger(__name__)


class DetectedSegment(TypedDict):
    start: float
    end: float
    duration: float


def humanize_segments(segments: list[DetectedSegment]) -> str:
    return ','.join([
        '-'.join(map(seconds_to_position,
                 [segment['start'], segment['end']]))
        for segment in segments
    ])


def merge_adjacent_segments(segments: list[DetectedSegment], min_gap=0.1, min_duration=1200.) -> list[DetectedSegment]:

    if len(segments) == 0:
        return []

    merged_segments = [segments[0],]

    for i in range(1, len(segments)):
        prev_segment, segment = segments[i-1], segments[i]
        if (gap := segment['start'] - prev_segment['end']) <= min_gap and segment['duration'] <= min_duration:
            merged_segments[-1] = DetectedSegment(
                start=merged_segments[-1]['start'],
                end=segment['end'],
                duration=merged_segments[-1]['duration'] + segment['duration'] + gap
            )
        else:
            merged_segments.append(segment)

    return [segment | {'duration': round(segment['duration'], 2)} for segment in merged_segments] # type: ignore


def run_segment_detectors(movie_path: Path, config):
    detectors = {
        # 'black': BlackDetect,
        # 'silence': SilenceDetect,
        # 'axcorrelate_silence': AudioCrossCorrelationDetect,
        'match_template': OpenCVTemplateDetectWithInjectedTemplate(movie_path, config)
    }
    detected_segments = {}

    for detector_key, detector_value in detectors.items():
        logger.info('Running %s detection...', detector_key)

        detector_instance = detector_value(movie_path)
        detector_result = cast(list[DetectedSegment], detector_instance.detect())
        detector_result = merge_adjacent_segments(detector_result)
        detected_segments[detector_key] = {
            "segments": detector_result,
            "humanized_segments": humanize_segments(detector_result)
        }

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
