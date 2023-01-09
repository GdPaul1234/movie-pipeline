from dataclasses import dataclass

from util import seconds_to_position


@dataclass(eq=True, order=True, frozen=True)
class Segment:
    start: float
    end: float

    def  __post_init__(self):
        if self.start > self.end:
            raise ValueError('Incoherent Segment')

    def __repr__(self) -> str:
        return ','.join((
            seconds_to_position(self.start),
            seconds_to_position(self.end),
            "{:02.0f}:{:02.0f}".format(*divmod(self.duration, 60))
        ))

    def is_overlapping(self, other_segment: 'Segment'):
        return (other_segment.start <= self.start <= other_segment.end \
            or other_segment.start <= self.end <= other_segment.end) \
            and other_segment != self

    @property
    def duration(self) -> float:
        return self.end - self.start


class SegmentContainer:
    _segments: set[Segment] = set()

    @property
    def segments(self):
        return tuple(sorted(self._segments))

    @staticmethod
    def check_validity(segments, new_segment: Segment):
        return not any(segment.is_overlapping(new_segment) for segment in segments)

    def add(self, segment: Segment):
        if self.check_validity(self._segments, segment):
            self._segments.add(segment)

    def remove(self, segment: Segment):
        self._segments.remove(segment)

    def edit(self, old_segment: Segment, new_segment: Segment):
        if self.check_validity([segment for segment in self._segments if segment != old_segment], new_segment):
            self._segments.remove(old_segment)
            self._segments.add(new_segment)

    def merge(self, segments: list[Segment]):
        self._segments -= set(segments)

        sorted_segments = sorted(segments)
        merged_segment = Segment(sorted_segments[0].start, sorted_segments[-1].end)
        self._segments.add(merged_segment)
