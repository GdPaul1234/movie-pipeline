from abc import ABC
from pathlib import Path
from typing import Generator, Optional

from ...lib.util import total_movie_duration
from ...models.detected_segments import DetectedSegment
from ...settings import Settings

class BaseDetect(ABC):
    def __init__(self, movie_path: Path, config: Settings) -> None:
        self._movie_path = movie_path
        self._config = config

    def should_proceed(self) -> bool:
        ...

    def detect_with_progress(
        self,
        target_fps=5.0,
        seek_ss: Optional[str | float] = None,
        seek_t: Optional[str | float] = None
    ) -> Generator[float, None, list[DetectedSegment]]:
        ...


class DummyDetect(BaseDetect):
    def should_proceed(self) -> bool:
        return True
    
    def detect_with_progress(
        self, 
        target_fps=5,
        seek_ss: str | float | None = None,
        seek_t: str | float | None = None
    ) -> Generator[float, None, list[DetectedSegment]]:
        yield 1.0

        padding_duration = self._config.SegmentDetection.padding_duration
        movie_duration = total_movie_duration(self._movie_path)

        start = padding_duration if padding_duration < movie_duration else 0
        end = movie_duration - start

        return [DetectedSegment(start=start, end=end, duration=end - start)]
