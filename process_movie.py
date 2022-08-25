import itertools
import logging
from schema import Schema, Regex
from pathlib import Path
import yaml
import ffmpeg

from movie_path_destination_finder import MoviePathDestinationFinder
from movie_file import LegacyMovieFile
from util import position_in_seconds

logger = logging.getLogger(__name__)

processed_data_schema = Schema({
    # valid filename of the output file with .mp4 suffix
    "filename": Regex(r"^[\w&àéèï',\s-]+\.mp4$"),
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
            movie_processed_data_path.read_text(encoding='utf-8'))
        processed_data_schema.validate(self._movie_processed_data)
        self._segments = []

    @property
    def segments(self) -> list[tuple[float, float]]:
        if not len(self._segments):
            raw_segments: str = self._movie_processed_data['segments']
            self._segments = [tuple(map(position_in_seconds, segment.split('-', 2)))
                              for segment in raw_segments.removesuffix(',').split(',')]
        return self._segments

    def _ffmpeg_segments(self, in_file, audio_streams):
        return itertools.chain.from_iterable(
            [(in_file.video.filter_('trim', start=segment[0], end=segment[1]).filter_('setpts', 'PTS-STARTPTS'),
              *[in_file[str(audio['index'])].filter_('atrim', start=segment[0], end=segment[1]).filter_('asetpts', 'PTS-STARTPTS')
                for audio in audio_streams],)
             for segment in self.segments])

    def process(self):
        in_file_path = Path(self._processed_data_path).with_suffix('')
        in_file = ffmpeg.input(str(in_file_path))
        probe = ffmpeg.probe(in_file_path)

        audio_streams = [stream for stream in probe['streams']
                         if stream.get('codec_type', 'N/A') == 'audio']
        nb_audio_streams = len(audio_streams)
        logger.debug(f'{nb_audio_streams=}')

        dest_filename = self._movie_processed_data['filename']
        dest_path = MoviePathDestinationFinder(
            LegacyMovieFile(dest_filename)).resolve_destination()
        dest_filepath = dest_path.joinpath(dest_filename)

        command = (
            ffmpeg
            .concat(*self._ffmpeg_segments(in_file, audio_streams), v=1, a=nb_audio_streams)
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

            out, err = command.run(
                cmd=['ffmpeg', '-hwaccel', 'cuda'],
                capture_stdout=True, capture_stderr=True)

            logger.debug(out.decode())
            logger.debug(err.decode())
            logger.info('Processing "%s" done', dest_filepath)
        except ffmpeg.Error as e:
            logger.exception(e.stderr.decode())


class MovieFileProcessorFolderRunner:
    @staticmethod
    def process_directory(folder_path: Path):
        logger.info('Processing: "%s"', folder_path)
        for p in folder_path.iterdir():
            if p.is_file() and p.suffix == '.yml':
                MovieFileProcessor(p).process()

        logger.info('Process all movie files in "%s"', folder_path)


def command(options):
    logger.debug('args: %s', vars(options))
    filepath = Path(options.file)

    try:
        if filepath.is_file() and filepath.suffix == '.yml':
            MovieFileProcessor(filepath).process()
        elif filepath.is_dir():
            MovieFileProcessorFolderRunner.process_directory(filepath)
        else:
            raise ValueError('Unknown file type')
    except Exception as e:
        logger.exception(e)
