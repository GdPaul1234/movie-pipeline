from typing import TypedDict

from ..lib.util import seconds_to_position


class DetectedSegment(TypedDict):
    start: float
    end: float
    duration: float


def humanize_segments(segments: list[DetectedSegment]) -> str:
    return ','.join([
        '-'.join(map(seconds_to_position, [segment['start'], segment['end']]))
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
