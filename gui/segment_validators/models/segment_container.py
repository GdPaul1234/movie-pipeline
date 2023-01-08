from dataclasses import dataclass


@dataclass(eq=True, order=True)
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
    _segments: list[Segment] = []

    @property
    def segments(self):
        return tuple(self._segments)

    def add(self, segment: Segment):
        self._segments.append(segment)
        self._segments.sort()

    def remove(self, segment: Segment):
        self._segments.remove(segment)
        self._segments.sort()
