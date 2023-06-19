from pathlib import Path
import yaml

from movie_pipeline.commands.scaffold_dir import available_title_strategies, channel_pattern

from ..models.segment_container import SegmentContainer
from movie_pipeline.commands.process_movie import edl_content_schema
from movie_pipeline.commands.scaffold_dir import PathScaffolder

from settings import Settings


def ensure_decision_file_template(source_path: Path, config: Settings):
    return PathScaffolder(source_path, config).scaffold()


def extract_title(source_path: Path, config: Settings):
    path_scaffolder = PathScaffolder(source_path, config)

    matches = channel_pattern.search(source_path.stem)

    if not matches:
        return 'Nom du fichier  converti.mp4'

    channel = matches.group(1)
    title_strategy_name = path_scaffolder._titles_strategies.get(channel) or 'NaiveTitleExtractor'
    title_strategy = available_title_strategies[title_strategy_name](path_scaffolder._title_cleaner)

    return title_strategy.extract_title(source_path)


class EditDecisionFileDumper:
    def __init__(
        self,
        title: str,
        source_path: Path,
        segment_container: SegmentContainer,
        config: Settings
    ) -> None:
        self._title = title
        self._source_path = source_path
        self._segment_container = segment_container
        self._config = config

    def dump_decision_file(self):
        ensure_decision_file_template(self._source_path, self._config)
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
