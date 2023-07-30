import json
from datetime import datetime
import logging
from pathlib import Path

from ..models.segment_container import SegmentContainer


logger = logging.getLogger(__name__)


def import_segments(source_path: Path):
    segments_path = source_path.with_suffix(f'{source_path.suffix}.segments.json')
    try:
        return json.loads(segments_path.read_text(encoding='utf-8'))
    except IOError:
        return {}


def prepend_last_segments_to_segment_file(source_path: Path, segment_container: SegmentContainer):
    segments_path = source_path.with_suffix(f'{source_path.suffix}.segments.json')

    if not segments_path.is_file():
        logger.warning(f'Missing segments file for "{str(source_path)}"')
        segments_path.write_text(json.dumps({ }), encoding='utf-8')

    segments_content = json.loads(segments_path.read_text(encoding='utf-8'))
    content = { f'result_{datetime.now().isoformat()}': repr(segment_container), **segments_content }

    segments_path.write_text(json.dumps(content, indent=2))
