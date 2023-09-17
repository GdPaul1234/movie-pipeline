import logging
from collections import deque
from pathlib import Path
from typing import Iterator

import ffmpeg
import yaml
from rich.progress import Progress
from schema import Optional, Regex, Schema
from abc import ABC

from settings import Settings
from util import position_in_seconds

from ..lib.backup_policy_executor import BackupPolicyExecutor, EdlFile
from ..lib.ffmpeg_with_progress import ffmpeg_command_with_progress
from ..lib.movie_path_destination_finder import MoviePathDestinationFinder
from ..lib.ui_factory import transient_task_progress
from ..models.movie_file import LegacyMovieFile
from ..models.movie_segments import MovieSegments

logger = logging.getLogger(__name__)


edl_content_schema = Schema({
    # valid filename of the output file with .mp4 suffix
    "filename": Regex(r"^[\w&àéèï'!()\[\], #-.]+\.mp4$"),
    # format: hh:mm:ss.ss-hh:mm:ss.ss,hh-mm:ss…
    "segments": Regex(r'(?:(?:\d{2}:\d{2}:\d{2}\.\d{2,3})-(?:\d{2}:\d{2}:\d{2}\.\d{2,3}),)+'),
    Optional("skip_backup", default=False): bool
})


class MovieFileProcessorStep(ABC):
    def __init__(self, context: 'MovieFileProcessor') -> None:
        self._context = context

    def handle(self) -> Iterator[float]:
        yield 1


class ProcessStep(MovieFileProcessorStep):
    def __init__(self, context: 'MovieFileProcessor') -> None:
        super().__init__(context)

    def handle(self):
        in_file = ffmpeg.input(str(self._context.in_file_path))
        probe = ffmpeg.probe(self._context.in_file_path)

        audio_streams = [stream for stream in probe['streams'] if stream.get('codec_type', 'N/A') == 'audio']
        nb_audio_streams = len(audio_streams)
        logger.debug(f'{nb_audio_streams=}')

        dest_path = MoviePathDestinationFinder(LegacyMovieFile(self._context.dest_filename), self._context.config).resolve_destination()
        dest_filepath = dest_path.joinpath(self._context.dest_filename)

        logger.info('Processing "%s" from "%s"...', dest_filepath, self._context.in_file_path)

        command = (
            ffmpeg
            .concat(
                *self._context.movie_segments.to_ffmpeg_concat_segments(in_file, audio_streams),
                v=1, a=nb_audio_streams
            )
            .output(
                str(dest_filepath),
                vcodec='h264_nvenc',
                **{'preset:v': 'p7', 'tune:v': 'hq', 'rc:v': 'vbr', 'cq:v': 28, 'profile:v': 'high'},
                acodec='aac', cutoff='20K', audio_bitrate='256K', ac=2,
                **{f'map_metadata:s:a:{index}': f'0:s:a:{index}' for index in range(nb_audio_streams)},
                dn=None, sn=None, ignore_unknown=None,
            )
        )

        try:
            logger.debug(f'{self._context.segments=}')
            logger.info('Running: %s', command.compile())

            total_seconds = self._context.movie_segments.total_seconds
            for item in ffmpeg_command_with_progress(command, cmd=['ffmpeg', '-hwaccel', 'cuda']):
                if item.get('time'):
                    processed_time = max(position_in_seconds(item['time']), 0)
                    yield processed_time / total_seconds

        except ffmpeg.Error as e:
            logger.exception(e.stderr)
            raise e

        return super().handle()


class BackupStep(MovieFileProcessorStep):
    def __init__(self, context: 'MovieFileProcessor') -> None:
        super().__init__(context)

    def handle(self):
        logger.info('Backuping "%s"...', self._context.dest_filename)
        self._context.backup_policy_executor.execute(original_file_path=self._context.in_file_path)
        return super().handle()


class MovieFileProcessor:
    def __init__(self, edl_path: Path, config: Settings, *, backup_policy_executor=BackupPolicyExecutor) -> None:
        """
        Args:
            edl_path (Path): path to edit decision list file
                (naming: {movie file with suffix}.txt)
        """
        edl_content = yaml.safe_load(edl_path.read_text(encoding='utf-8'))
        edl_content = edl_content_schema.validate(edl_content)
        edl_file = EdlFile(edl_path, edl_content)

        self.backup_policy_executor = backup_policy_executor(edl_file, config)

        self.movie_segments = MovieSegments(raw_segments=edl_file.content['segments'])
        self.segments = self.movie_segments.segments
        self.config = config

        self.in_file_path = edl_file.path.with_suffix('')
        self.dest_filename = edl_file.content['filename']

    def process(self):
        deque(self.process_with_progress(), maxlen=0)

    def process_with_progress(self):
        logger.info(self.dest_filename)
        for process_progress_percent in ProcessStep(self).handle():
            yield 0.8 * process_progress_percent

        for backup_progress_percent in BackupStep(self).handle():
            yield 0.8 + 0.2 * backup_progress_percent

        logger.info('"%s" processed sucessfully', self.dest_filename)

    def process_with_progress_tui(self, progress: Progress):
        with transient_task_progress(progress, description=self.dest_filename, total=1.0) as task_id:
            for process_progress_percent in ProcessStep(self).handle():
                yield 0.8 * process_progress_percent
                progress.update(task_id, completed=process_progress_percent)

        with transient_task_progress(progress, f'Backuping {self.dest_filename}...'):
            for backup_progress_percent in BackupStep(self).handle():
             yield 0.8 + 0.2 * backup_progress_percent

        logger.info('"%s" processed sucessfully', self.dest_filename)

