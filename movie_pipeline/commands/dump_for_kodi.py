import logging
from pathlib import Path

from movie_pipeline.services.kodi_dumper import KodiDumper

from settings import Settings

logger = logging.getLogger(__name__)

def command(options, config: Settings):
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
                try:
                    dump_to_nfo(file)
                except Exception as e:
                    logger.warning('Skipping "%s"', file)
                    logger.exception(e)
        else:
            raise ValueError('Unknown file type')
    except Exception as e:
        logger.exception(e)
