from pathlib import Path
import yaml

from ..models.segment_container import SegmentContainer
from movie_pipeline.commands.process_movie import edl_content_schema
from movie_pipeline.commands.scaffold_dir import PathScaffolder


class EditDecisionFileDumper:
    def __init__(self, title: str, source_path: Path, segment_container: SegmentContainer, config) -> None:
        self._title = title
        self._source_path = source_path
        self._segment_container = segment_container
        self._config = config

    def _ensure_decision_file_template(self):
        PathScaffolder(self._source_path, self._config).scaffold()

    def dump_decision_file(self):
        self._ensure_decision_file_template()
        decision_file_path = self._source_path.with_suffix(f'{self._source_path.suffix}.yml')

        decision_file_content = {
            'filename': self._title,
            'segments': f'{repr(self._segment_container)},'
        }

        if edl_content_schema.is_valid(decision_file_content):
            decision_file_path.write_text(yaml.safe_dump(decision_file_content), encoding='utf-8')
            decision_file_path.with_suffix('.yml.txt').unlink()
            return decision_file_path

        return None
