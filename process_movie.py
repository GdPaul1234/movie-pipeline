import typing
import concurrent.futures
import binpacking
import itertools
import logging
import shutil
from schema import Schema, Optional, Regex
from pathlib import Path
import yaml
import ffmpeg

from movie_path_destination_finder import MoviePathDestinationFinder
from movie_file import LegacyMovieFile
from util import position_in_seconds

logger = logging.getLogger(__name__)

edl_content_schema = Schema({
    # valid filename of the output file with .mp4 suffix
    "filename": Regex(r"^[\w&àéèï'!(), -.]+\.mp4$"),
    # format: hh:mm:ss.ss-hh:mm:ss.ss,hh-mm:ss…
    "segments": Regex(r'(?:(?:\d{2}:\d{2}:\d{2}\.\d{2,3})-(?:\d{2}:\d{2}:\d{2}\.\d{2,3}),)+'),
    Optional("skip_backup", default=False): bool
})


class MovieFileProcessor:
    def __init__(self, edl_path: Path, config) -> None:
        """
        Args:
            edl_path (Path): path to edit decision list file
                (naming: {movie file with suffix}.txt)
        """
        self._edl_path = edl_path
        self._edl_content = yaml.safe_load(edl_path.read_text(encoding='utf-8'))
        edl_content_schema.validate(self._edl_content)
        self._segments = []
        self._config = config

    @property
    def segments(self) -> list[tuple[float, float]]:
        if not len(self._segments):
            raw_segments: str = self._edl_content['segments']
            self._segments = [tuple(map(position_in_seconds, segment.split('-', 2)))
                              for segment in raw_segments.removesuffix(',').split(',')]
        return self._segments

    def _ffmpeg_segments(self, in_file, audio_streams):
        return itertools.chain.from_iterable(
            [(in_file.video.filter_('trim', start=segment[0], end=segment[1]).filter_('setpts', 'PTS-STARTPTS'),
              *[in_file[str(audio['index'])].filter_('atrim', start=segment[0], end=segment[1]).filter_('asetpts', 'PTS-STARTPTS')
                for audio in audio_streams],)
             for segment in self.segments])

    def archive_or_delete_if_serie_original_file(self, original_file_path: Path):
        backup_folder = self._config.get('Paths', 'backup_folder', fallback=None)
        skip_backup = self._edl_content.get('skip_backup', False)

        if skip_backup or backup_folder is None:
            # Inactivate processing decision file
            logger.info(
                'No backup folder found in config or backup is disabled for this file'
                ', inactivate processing decision file')
            self._edl_path.rename(self._edl_path.with_suffix('.yml.done'))
        else:
            # Move original file to archive
            backup_folder_path = Path(backup_folder)
            original_movie = LegacyMovieFile(self._edl_content['filename'])

            if original_movie.is_serie:
                logger.info('%s is serie, deleting it', original_file_path)
                original_file_path.unlink()
                self._edl_path.unlink()
            else:
                dest_path = backup_folder_path.joinpath(original_movie.title)
                dest_path.mkdir()

                logger.info('Move "%s" to "%s"', original_file_path, dest_path)
                shutil.move(original_file_path, dest_path)
                shutil.move(self._edl_path, dest_path)

    def process(self):
        in_file_path = self._edl_path.with_suffix('')
        in_file = ffmpeg.input(str(in_file_path))
        probe = ffmpeg.probe(in_file_path)

        audio_streams = [stream for stream in probe['streams']
                         if stream.get('codec_type', 'N/A') == 'audio']
        nb_audio_streams = len(audio_streams)
        logger.debug(f'{nb_audio_streams=}')

        dest_filename = self._edl_content['filename']
        dest_path = MoviePathDestinationFinder(LegacyMovieFile(dest_filename), self._config).resolve_destination()
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

            self.archive_or_delete_if_serie_original_file(in_file_path)
            logger.info('"%s" processed sucessfully', dest_filepath)
        except ffmpeg.Error as e:
            logger.exception(e.stderr.decode())


class MovieFileProcessorFolderRunner:
    def __init__(self, folder_path: Path, edl_ext: str, config) -> None:
        self._folder_path = folder_path
        self._edl_ext = edl_ext
        self._config = config

        self._nb_worker = self._config.getint('Processor', 'nb_worker', fallback=1)

    def _distribute_fairly_edl(self):
        edls = list(self._folder_path.glob(f'*{self._edl_ext}'))

        if len(edls) == 0:
            return list(itertools.repeat([], times=self._nb_worker))

        return binpacking.to_constant_bin_number(
            edls,
            N_bin=self._nb_worker,
            key=lambda f: f.with_suffix('').stat().st_size
        )

    def _prepare_processing(self):
        for index, group in enumerate(self._distribute_fairly_edl()):
            # rename distributed edls
            for edl in typing.cast(list[Path], group):
                new_edl_name = edl.with_suffix(f'.pending_yml_{index}')
                edl.rename(new_edl_name)
                logger.info('  acknowledge %s', new_edl_name)


    def _execute_processing(self, edl_ext: str):
        for edl in self._folder_path.glob(f'*{edl_ext}'):
            MovieFileProcessor(edl, self._config).process()

    def process_directory(self):
        logger.info('Processing: "%s"', self._folder_path)

        self._prepare_processing()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._nb_worker) as executor:
            future_tasks = {
                executor.submit(self._execute_processing, edl_ext): edl_ext
                for edl_ext in map(lambda index: f'.pending_yml_{index}', range(self._nb_worker))
            }

            for future in concurrent.futures.as_completed(future_tasks):
                edl_ext = future_tasks[future]
                try:
                    future.result() # wait for completion
                except Exception as e:
                    logger.error('Exception when processing *%s files: %s', edl_ext, e)
                    raise e
                else:
                    logger.info('Processed all %s edl files', edl_ext)

        logger.info('All movie files in "%s" processed', self._folder_path)


def command(options, config):
    logger.debug('args: %s', vars(options))

    filepath = Path(options.file)
    edl_ext: str = options.custom_ext

    try:
        if filepath.is_file() and filepath.suffix == edl_ext:
            MovieFileProcessor(filepath, config).process()
        elif filepath.is_dir():
            MovieFileProcessorFolderRunner(filepath, edl_ext, config).process_directory()
        else:
            raise ValueError('Unknown file type')
    except Exception as e:
        logger.exception(e)
