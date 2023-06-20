import json
import yaml
from pathlib import Path
from datetime import datetime

from ..models.segment_container import SegmentContainer

class SegmentImporter:
    def __init__(self, source_path: Path) -> None:
        self._source_path = source_path

    def import_segments(self):
        segments_path = self._source_path.with_suffix(f'{self._source_path.suffix}.segments.json')
        try:
            return json.loads(segments_path.read_text(encoding='utf-8'))
        except IOError:
            return {}


def prepend_last_segments_to_segment_file(source_path: Path):
    segments_path = source_path.with_suffix(f'{source_path.suffix}.segments.json')
    edl_path = source_path.with_suffix(f'{source_path.suffix}.yml')

    if not segments_path.is_file() or not edl_path.is_file():
        raise ValueError(f'Missing segments or edl file for "{str(source_path)}"')

    segments_content = json.loads(segments_path.read_text(encoding='utf-8'))
    edl_content = yaml.safe_load(edl_path.read_text(encoding='utf-8'))
    content = { f'result_{datetime.now().isoformat()}': edl_content['segments'], **segments_content }

    segments_path.write_text(json.dumps(content, indent=2))
