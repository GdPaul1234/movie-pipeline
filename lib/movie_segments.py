from dataclasses import dataclass
import itertools
from util import position_in_seconds

@dataclass
class MovieSegments:
    segments: list[tuple[float, float]]

    def __init__(self, raw_segments: str) -> None:
        self.segments = [tuple(map(position_in_seconds, segment.split('-', 2)))
                         for segment in raw_segments.removesuffix(',').split(',')]

    @property
    def total_seconds(self) -> float:
        return sum([stop - start for start, stop in self.segments])

    def to_ffmpeg_concat_segments(self, in_file, audio_streams):
        return itertools.chain.from_iterable(
            [(in_file.video.filter_('trim', start=segment[0], end=segment[1]).filter_('setpts', 'PTS-STARTPTS'),
              *[in_file[str(audio['index'])].filter_('atrim', start=segment[0], end=segment[1]).filter_('asetpts', 'PTS-STARTPTS')
                for audio in audio_streams],)
             for segment in self.segments])

