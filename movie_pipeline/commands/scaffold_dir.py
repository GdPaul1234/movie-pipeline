import logging
from pathlib import Path
from schema import Schema
import re
import yaml

from ..lib.title_cleaner import TitleCleaner
from ..lib.title_extractor import (
    NaiveTitleExtractor,
    SerieSubTitleAwareTitleExtractor,
    SerieTitleAwareTitleExtractor,
    SubtitleTitleExpanderExtractor
)

logger = logging.getLogger(__name__)


class MovieProcessedFileGenerator:
    def __init__(self, movie_file_path: Path, title_extractor: NaiveTitleExtractor) -> None:
        self._movie_file_path = movie_file_path
        self._title_extractor = title_extractor

    def extract_title(self) -> str:
        return self._title_extractor.extract_title(self._movie_file_path)

    def generate(self):
        movie_file_suffix = self._movie_file_path.suffix
        processed_file = self._movie_file_path.with_suffix(f'{movie_file_suffix}.yml.txt')

        logger.info('Generate "%s"', processed_file)
        processed_file.write_text(
            f"filename: {self.extract_title()}.mp4\n"
            "segments: INSERT_SEGMENTS_HERE\n", encoding='utf-8')


channel_pattern = re.compile(r'^([^_]+)_')
available_title_strategies = {
    'NaiveTitleExtractor': NaiveTitleExtractor,
    'SubtitleTitleExpanderExtractor': SubtitleTitleExpanderExtractor,
    'SerieSubTitleAwareTitleExtractor': SerieSubTitleAwareTitleExtractor,
    'SerieTitleAwareTitleExtractor': SerieTitleAwareTitleExtractor
}

title_strategies_schema = Schema({
    str: lambda strategy: strategy in available_title_strategies.keys()
})

class PathScaffolder:
    def __init__(self, path: Path, config) -> None:
        self._path = path
        self._config = config

        title_strategies_path = Path(config.get('Paths', 'title_strategies', fallback='invalid path'))

        if title_strategies_path.exists():
            titles_strategies = yaml.safe_load(title_strategies_path.read_text('utf-8'))
            self._titles_strategies = title_strategies_schema.validate(titles_strategies)
        else:
            self._titles_strategies = {}

        if (blacklist_path := Path(config.get('Paths', 'title_re_blacklist'))).exists():
            self._title_cleaner = TitleCleaner(blacklist_path)
        else:
            raise FileNotFoundError(blacklist_path)

    def _generate_file(self, file: Path) -> bool:
        if len(list(file.parent.glob(f'{file.name}.*yml'))): return False

        matches = channel_pattern.search(file.stem)

        if not matches:
            logger.warning('Skipping "%s" because its filename does not match the required pattern', file)
            return False

        channel = matches.group(1)
        title_strategy_name = self._titles_strategies.get(channel) or 'NaiveTitleExtractor'
        title_strategy = available_title_strategies[title_strategy_name](self._title_cleaner)

        MovieProcessedFileGenerator(file, title_strategy).generate()
        return True

    def _scaffold_dir(self) -> bool:
        return all(self._generate_file(file) for file in self._path.glob('*.ts'))

    def scaffold(self):
        return self._scaffold_dir() if self._path.is_dir() else self._generate_file(self._path)


def command(options, config):
    logger.debug('args: %s', vars(options))
    dir_path = Path(options.dir)

    try:
        PathScaffolder(dir_path, config).scaffold()
    except Exception as e:
        logger.exception(e)
