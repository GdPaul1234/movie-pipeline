import asyncio
import logging
from schema import Schema, Regex
from pathlib import Path
import yaml
import ffmpeg

from config_loader import ConfigLoader
from movie_path_destination_finder import MoviePathDestinationFinder
from movie_file import LegacyMovieFile
from util import position_in_seconds

logger = logging.getLogger(__name__)

processed_data_schema = Schema({
    # valid filename of the output file with .mp4 suffix
    "filename": Regex(r'^[\w,\s-]+\.mp4$'),
    # format: hh:mm:ss.ss-hh:mm:ss.ss,hh-mm:ss…
    "segments": Regex(r'(?:(?:\d{2}:\d{2}:\d{2}\.\d{2,3})-(?:\d{2}:\d{2}:\d{2}\.\d{2,3}),)+')
})


class MovieFileProcessor:
    def __init__(self, movie_processed_data_path: Path) -> None:
        """
        Args:
            movie_processed_data_path (Path): path to processed_data file path 
                (naming: {movie file with suffix}.txt)
        """
        self._processed_data_path = movie_processed_data_path
        self._movie_processed_data = yaml.safe_load(
            movie_processed_data_path.read_text())
        processed_data_schema.validate(self._movie_processed_data)
        self._segments = []

    @property
    def segments(self) -> list[tuple[str, str]]:
        if not len(self._segments):
            raw_segments: str = self._movie_processed_data['segments']
            self._segments = [tuple(map(position_in_seconds ,segment.split('-', 2)))
                              for segment in raw_segments.removesuffix(',').split(',')]
        return self._segments

    def process(self):
        in_file = ffmpeg.input(
            str(Path(self._processed_data_path).with_suffix('')))

        dest_filename = self._movie_processed_data['filename']
        dest_path = MoviePathDestinationFinder(
            LegacyMovieFile(dest_filename)).resolve_destination()
        dest_filepath = dest_path.joinpath(dest_filename)

        command = (
            ffmpeg
            .concat(
                *[in_file.trim(start=segment[0], end=segment[1])
                  for segment in self.segments]
            )
            .output(
                str(dest_filepath),
                vcodec='h264_nvenc',
                acodec='aac', cutoff='20K', audio_bitrate='256K', ac=2,
                dn=None, sn=None, ignore_unknown=None
            )
        )

        try:
            logger.debug(f'{self._segments=}')
            logger.info('Running: %s', command.compile())
            command.run(capture_stderr=True)
            logger.info('Processing "%s" done', dest_filepath)
        except ffmpeg.Error as e:
            logger.exception(e.stderr.decode())

    async def process_async(self, folder_runner: 'MovieFileProcessorFolderRunner'):
        async with folder_runner.sem_max_tasks:
            self.process()


class MovieFileProcessorFolderRunner:
    def __init__(self, ) -> None:
        max_tasks = ConfigLoader().config.getint('Processor', 'max_tasks', fallback=2)
        self.sem_max_tasks = asyncio.Semaphore(max_tasks)

    async def process_directory(self, folder_path: Path):
        logger.info('Processing: "%s"', folder_path)
        tasks = [MovieFileProcessor(p).process_async(self)
                 for p in self._folder_path.iterdir()
                 if p.is_file() and p.suffix == '.yml']

        await asyncio.gather(*tasks)
        logger.info('Process all movie file in "%s"', self._folder_path)


def command(options):
    logger.debug('args: %s', vars(options))
    filepath = Path(options.file)

    try:
        if filepath.is_file() and filepath.suffix == '.yml':
            MovieFileProcessor(filepath).process()
        elif filepath.is_dir():
            asyncio.run(MovieFileProcessorFolderRunner()
                        .process_directory(filepath))
        else:
            raise ValueError('Unknown file type')
    except Exception as e:
        logger.exception(e)
