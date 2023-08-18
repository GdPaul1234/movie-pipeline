import logging
from collections import deque
from pathlib import Path

import ffmpeg
import yaml
from rich.progress import Progress
from schema import Optional, Regex, Schema

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


class MovieFileProcessor:
    def __init__(
        self,
        edl_path: Path,
        progress: Progress,
        config: Settings,
        *,
        backup_policy_executor=BackupPolicyExecutor
    ) -> None:
        """
        Args:
            edl_path (Path): path to edit decision list file
                (naming: {movie file with suffix}.txt)
        """
        edl_content = yaml.safe_load(edl_path.read_text(encoding='utf-8'))
        edl_content = edl_content_schema.validate(edl_content)
        self._edl_file = EdlFile(edl_path, edl_content)

        self._progress = progress
        self._backup_policy_executor = backup_policy_executor(self._edl_file, config)

        self._movie_segments = MovieSegments(raw_segments=self._edl_file.content['segments'])
        self._segments = self._movie_segments.segments
        self._config = config

    def process(self):
        deque(self.process_with_progress(), maxlen=0)

    def process_with_progress(self):
        in_file_path = self._edl_file.path.with_suffix('')
        in_file = ffmpeg.input(str(in_file_path))
        probe = ffmpeg.probe(in_file_path)

        audio_streams = [stream for stream in probe['streams'] if stream.get('codec_type', 'N/A') == 'audio']
        nb_audio_streams = len(audio_streams)
        logger.debug(f'{nb_audio_streams=}')

        dest_filename = self._edl_file.content['filename']
        dest_path = MoviePathDestinationFinder(LegacyMovieFile(dest_filename), self._config).resolve_destination()
        dest_filepath = dest_path.joinpath(dest_filename)

        command = (
            ffmpeg
            .concat(
                *self._movie_segments.to_ffmpeg_concat_segments(in_file, audio_streams),
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
            logger.debug(f'{self._segments=}')
            logger.info('Running: %s', command.compile())

            total_seconds = self._movie_segments.total_seconds
            with transient_task_progress(self._progress, description=dest_filename, total=total_seconds) as task_id:
                for item in ffmpeg_command_with_progress(command, cmd=['ffmpeg', '-hwaccel', 'cuda']):
                    if item.get('time'):
                        processed_time = position_in_seconds(item['time'])
                        yield 0.8 * (processed_time / total_seconds)
                        self._progress.update(task_id, completed=processed_time)

            with transient_task_progress(self._progress, f'Backuping {dest_filename}...'):
                self._backup_policy_executor.execute(original_file_path=in_file_path)

            yield 1.0
            self._progress.update(task_id, completed=total_seconds)

            logger.info('"%s" processed sucessfully', dest_filepath)
        except ffmpeg.Error as e:
            logger.exception(e.stderr)
            raise e
