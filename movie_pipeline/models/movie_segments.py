from dataclasses import dataclass
import itertools
from typing import cast

from ..lib.util import position_in_seconds


segment_t = tuple[float, float]


@dataclass
class MovieSegments:
    segments: list[segment_t]

    def __init__(self, raw_segments: str) -> None:
        splitted_raw_segments = raw_segments.removesuffix(',').split(',')

        self.segments = [
            cast(segment_t, tuple(position_in_seconds(x) for x in segment.split('-', 2)))
            for segment in splitted_raw_segments
        ] if splitted_raw_segments != [''] else []

    @property
    def total_seconds(self) -> float:
        return sum([stop - start for start, stop in self.segments])

    def to_ffmpeg_concat_segments(self, in_file, audio_streams):
        return itertools.chain.from_iterable(
            (
                # concat video stream
                in_file.video.filter_('trim', start=start, end=end).filter_('setpts', 'PTS-STARTPTS'),
                # concat audio streams
                *(
                    in_file[str(audio['index'])].filter_('atrim', start=start, end=end).filter_('asetpts', 'PTS-STARTPTS')
                    for audio in audio_streams
                )
            )
            for start, end in self.segments
        )
