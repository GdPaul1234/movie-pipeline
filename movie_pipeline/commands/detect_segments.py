import logging
from pathlib import Path

from ..lib.util import debug
from ..services.segments_detector.segments_detector import dump_segments_to_file, run_segment_detectors
from ..settings import Settings

logger = logging.getLogger(__name__)


@debug(logger)
def command(filepath: Path, selected_detectors_keys: list[str], config: Settings):
    try:
        if filepath.is_file():
            detectors_result = run_segment_detectors(filepath, selected_detectors_keys, config)
            dump_segments_to_file(detectors_result, movie_path=filepath)
        elif filepath.is_dir():
            for metadata_path in filepath.glob('*.metadata.json'):
                movie_path = metadata_path.with_name(f"{metadata_path.name.removesuffix('.metadata.json')}")
                logger.info('Search segments in "%s"...', movie_path)

                if not movie_path.with_suffix(f'{movie_path.suffix}.segments.json').exists():
                    detectors_result = run_segment_detectors(movie_path, selected_detectors_keys, config)
                    dump_segments_to_file(detectors_result, movie_path)
                else:
                    logger.warning('Segments already exist, skipping "%s"', movie_path)
        else:
            raise ValueError('File is not a movie')
    except Exception as e:
        logger.exception(e)
