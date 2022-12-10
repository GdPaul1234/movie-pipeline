from pathlib import Path
import re


class TitleCleaner:
    def __init__(self, blacklist_path: Path) -> None:
        blacklist = blacklist_path.read_text()
        self._blacklist_pattern = re.compile('|'.join(blacklist.splitlines()))

    def clean_title(self, title: str) -> str:
        return self._blacklist_pattern.sub('', title).strip()
