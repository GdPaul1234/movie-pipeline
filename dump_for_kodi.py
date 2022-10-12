import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from lib.vsmeta_parser import VsMetaParser

file_loader = FileSystemLoader('templates')
env = Environment(loader=file_loader)
env.trim_blocks = True
env.lstrip_blocks = True

logger = logging.getLogger(__name__)


class KodiDumper:
    def __init__(self, filepath: Path, nfo_filepath: Path):
        self._filepath = filepath
        self._nfo_filepath = nfo_filepath  # should not exist

    def dump_to_nfo(self):
        logger.info('Dumping "%s" to .nfo', self._filepath)

        parser = VsMetaParser(self._filepath)
        parsed_data = parser.parse()

        if parser.media_type not in ['movie', 'serie']:
            logger.info('"%s" is type Other, skipping', self._filepath.name)
            return

        template = env.get_template(f'kodi_{parser.media_type}.xml.jinja')
        output = template.render(parsed_data)

        self._nfo_filepath.write_text(output, encoding='utf-8')
        logger.info('"%s" created',  self._nfo_filepath)


def command(options):
    logger.debug('args: %s', vars(options))
    filepath = Path(options.file)

    def dump_to_nfo(filepath: Path):
        nfo_filepath = filepath\
            .with_name(filepath.stem.removesuffix(filepath.suffixes[0])) \
            .with_suffix('.nfo')
        if not nfo_filepath.exists():
            KodiDumper(filepath, nfo_filepath).dump_to_nfo()

    try:
        if filepath.is_file() and filepath.suffix == '.vsmeta':
            dump_to_nfo(filepath)
        elif filepath.is_dir():
            for file in filepath.glob('**/*.vsmeta'):
                dump_to_nfo(file)
        else:
            raise ValueError('Unknown file type')
    except Exception as e:
        logger.exception(e)
