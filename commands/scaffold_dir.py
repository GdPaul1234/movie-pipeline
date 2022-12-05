import logging
from pathlib import Path
import re
import yaml

from lib.title_extractor import NaiveTitleExtractor

logger = logging.getLogger(__name__)


class MovieProcessedFileGenerator:
    def __init__(self, movie_file_path: Path, title_extractor = NaiveTitleExtractor) -> None:
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
available_title_strategies = { 'NaiveTitleExtractor': NaiveTitleExtractor }

class DirScaffolder:
    def __init__(self, dir_path: Path, config) -> None:
        self._dir_path = dir_path
        self._config = config

        title_strategies_path = Path(config.get('Paths', 'title_strategies', fallback='invalid path'))

        if title_strategies_path.exists():
            self._titles_strategies = yaml.safe_load(title_strategies_path.read_text('utf-8'))
            # TODO: validate title strategies schema
        else:
            self._titles_strategies = {}

    def scaffold_dir(self):
        if not self._dir_path.is_dir():
            raise ValueError(f'dir_path must be a dir')

        for file in self._dir_path.glob('*.ts'):
            if not len(list(file.parent.glob(f'{file.name}.*'))):
                matches = channel_pattern.search(file.stem)

                if not matches:
                    logger.warning('Skipping "%s" because its filename does not match the required pattern', file)
                    continue

                channel = matches.group(1)
                title_strategy_name = self._titles_strategies.get(channel) or 'NaiveTitleExtractor'
                title_strategy = available_title_strategies[title_strategy_name]

                MovieProcessedFileGenerator(file, title_strategy).generate()


def command(options, config):
    logger.debug('args: %s', vars(options))
    dir_path = Path(options.dir)

    try:
        DirScaffolder(dir_path, config).scaffold_dir()
    except Exception as e:
        logger.exception(e)
