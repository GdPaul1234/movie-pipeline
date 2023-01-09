from dataclasses import dataclass


@dataclass(eq=True, order=True, frozen=True)
class Segment:
    start: float
    end: float

    def  __post_init__(self):
        if self.start > self.end:
            raise ValueError('Incoherent Segment')

    @property
    def duration(self) -> float:
        return self.end - self.start


class SegmentContainer:
    _segments: set[Segment] = set()

    @property
    def segments(self):
        return tuple(sorted(self._segments))

    def add(self, segment: Segment):
        self._segments.add(segment)

    def remove(self, segment: Segment):
        self._segments.remove(segment)

    def edit(self, old_segment: Segment, new_segment: Segment):
        self._segments.remove(old_segment)
        self._segments.add(new_segment)

    def merge(self, segments: list[Segment]):
        self._segments -= set(segments)

        sorted_segments = sorted(segments)
        merged_segment = Segment(sorted_segments[0].start, sorted_segments[-1].end)
        self._segments.add(merged_segment)
