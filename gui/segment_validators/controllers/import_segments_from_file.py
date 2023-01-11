import json
from pathlib import Path


class SegmentImporter:
    def __init__(self, source_path: Path) -> None:
        self._source_path = source_path

    def import_segments(self):
        segments_path = self._source_path.with_suffix(f'{self._source_path.suffix}.segments.json')
        try:
            return json.loads(segments_path.read_text(encoding='utf-8'))
        except IOError:
            return {}
