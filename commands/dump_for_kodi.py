import hashlib
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
        logger.info('"%s" created', path)

    def _render_image(self, image_type: str, image: bytes, md5: str, path: Path, auto_path=False):
        image_path = path.with_name(f'{path.stem}-{image_type}.jpg') if auto_path else path
        if not image_path.exists():
            image_md5 = hashlib.md5(image).hexdigest()
            if image_md5 != md5:
                raise IOError('"%s" would be corrupted, aborted', image_path)
            image_path.write_bytes(image)
            logger.info('"%s" written', image_path)

    def dump_to_nfo(self):
        logger.info('Dumping "%s" to .nfo', self._filepath)

        parser = VsMetaParser(self._filepath)
        parsed_data = parser.parse()

        if parser.media_type not in ['movie', 'serie']:
            logger.info('"%s" is type Other, skipping', self._filepath.name)
            return

        self._render_nfo(parser.media_type, parsed_data, self._nfo_filepath)
        self._render_image('poster' if parser.media_type == 'movie' else 'thumb',
                           parsed_data['poster_data'], parsed_data['poster_md5'],
                           self._nfo_filepath, auto_path=True)
        if parser.media_type == 'movie':
            try:
                self._render_image('fanart', parsed_data['backdrop']['image'][0],
                                   parsed_data['backdrop']['image_md5'][0],
                                   self._nfo_filepath, auto_path=True)
            except KeyError:
                logger.info('No fanart found in "%s"', self._filepath)

        else:
            tvshow_nfo_path = self._nfo_filepath.parent.parent.joinpath('tvshow.nfo')
            if not tvshow_nfo_path.exists():
                self._render_nfo('tvshow', parsed_data, tvshow_nfo_path)
                self._render_image('poster', parsed_data['tv_data']['poster_data'],
                                   parsed_data['tv_data']['poster_md5'],
                                   tvshow_nfo_path.with_name('poster.jpg'))
                self._render_image('fanart', parsed_data['tv_data']['backdrop']['image'][0],
                                   parsed_data['tv_data']['backdrop']['image_md5'][0],
                                   tvshow_nfo_path.with_name('fanart.jpg'))


def command(options, config):
    logger.debug('args: %s', vars(options))
    filepath = Path(options.file)

    def dump_to_nfo(filepath: Path):
        nfo_filepath = filepath \
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
