from pathlib import Path
from typing import cast
import re

title_pattern = re.compile(r"_([\w&àéèï'!., ()-]+)_")

class NaiveTitleExtractor:
    @staticmethod
    def extract_title(movie_file_path: Path) -> str:
        matches = title_pattern.search(movie_file_path.stem)
        return cast(re.Match[str], matches).group(1)

