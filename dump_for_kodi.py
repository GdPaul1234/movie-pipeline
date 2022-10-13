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

    def _render_nfo(self, media_type: str, parsed_data, path: Path):
        template = env.get_template(f'kodi_{media_type}.xml.jinja')
        output = template.render(parsed_data)

        path.write_text(output, encoding='utf-8')
        logger.info('"%s" created',  path)

    def dump_to_nfo(self):
        logger.info('Dumping "%s" to .nfo', self._filepath)

        parser = VsMetaParser(self._filepath)
        parsed_data = parser.parse()

        if parser.media_type not in ['movie', 'serie']:
            logger.info('"%s" is type Other, skipping', self._filepath.name)
            return

        self._render_nfo(parser.media_type, parsed_data, self._nfo_filepath)

        if parser.media_type == 'serie':
            tvshow_nfo_path = self._nfo_filepath.parent.parent.joinpath('tvshow.nfo')
            if not tvshow_nfo_path.exists():
                self._render_nfo('tvshow', parsed_data, tvshow_nfo_path)


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
