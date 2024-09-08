from abc import ABC
from pathlib import Path
from typing import Generator, Optional

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
