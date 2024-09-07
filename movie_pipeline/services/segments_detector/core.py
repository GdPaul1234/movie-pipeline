from abc import ABC
from pathlib import Path
from typing import Generator

from ...models.detected_segments import DetectedSegment
from ...settings import Settings

class BaseDetect(ABC):
    def __init__(self, movie_path: Path, config: Settings) -> None:
        self._movie_path = movie_path
        self._config = config

    def should_proceed(self) -> bool:
        return True

    def detect_with_progress(self) -> Generator[float, None, list[DetectedSegment]]:
        ...
