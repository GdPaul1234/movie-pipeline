from pathlib import Path
import re


class LegacyMovieFile:
    def __init__(self, filepath: str) -> None:
        self._filepath = Path(filepath)
        self._full_title = self._filepath.name

    @property
    def is_serie(self) -> bool:
        return re.search(r'S\d{2}E\d{2,}$', self.title) is not None

    @property
    def title(self) -> str:
        return self._filepath.stem

    def as_path(self) -> Path:
        return self._filepath
