import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class MovieProcessedFileGenerator:
    def __init__(self, movie_file: Path) -> None:
        self._movie_file = movie_file

    def extract_title(self) -> str:
        matches = re.search(r"_([\w&àéèï'!., ()-]+)_", self._movie_file.stem)
        return matches.group(1)

    def generate(self):
        movie_file_suffix = self._movie_file.suffix
        processed_file = self._movie_file.with_suffix(f'{movie_file_suffix}.yml.txt')

        logger.info('Generate "%s"', processed_file)
        processed_file.write_text(
            f"filename: {self.extract_title()}.mp4\n"
            "segments: INSERT_SEGMENTS_HERE\n", encoding='utf-8')


def command(options, config):
    logger.debug('args: %s', vars(options))
    dir_path = Path(options.dir)

    try:
        for file in dir_path.iterdir():
            if file.suffix == '.ts' and not file.with_suffix('.ts.yml').exists():
                MovieProcessedFileGenerator(file).generate()
    except Exception as e:
        logger.exception(e)
