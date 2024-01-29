from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Iterator, Optional

import ffmpeg
from abc import ABC
from movie_pipeline.lib.backup_policy_executor import BackupPolicyExecutor
from movie_pipeline.models.movie_segments import MovieSegments
from settings import Settings
from util import position_in_seconds

from ...lib.ffmpeg.ffmpeg_with_progress import ffmpeg_command_with_progress
from ...lib.movie_path_destination_finder import MoviePathDestinationFinder
from ...models.movie_file import LegacyMovieFile

logger = logging.getLogger(__name__)


@dataclass
class StepProgressResult:
    current_step: 'BaseStep'
    current_step_percent: float
    total_percent: float


@dataclass
class MovieFileProcessorContext:
    backup_policy_executor: BackupPolicyExecutor
    movie_segments: MovieSegments
    config: Settings
    in_file_path: Path
    dest_filename: str

@dataclass
class BaseStep(ABC):
    context: MovieFileProcessorContext
    description: str
    cost: float
    next_step: Optional['BaseStep']

    @property
    def all_steps(self) -> list['BaseStep']:
        visited_steps: list[BaseStep] = []
        visited_step = self

        while visited_step is not None:
            visited_steps.append(visited_step)
            visited_step = visited_step.next_step

        return visited_steps

    @property
    def total_cost(self) -> float:
        return sum(step.cost for step in self.all_steps)

    def handle(self) -> Iterator[float]:
        yield 1

    def process_all(self) -> Iterator[StepProgressResult]:
        total_cost = self.total_cost

        completed_percent = 0.0
        current_step = self

        while current_step is not None:
            total_normalized_current_cost = current_step.cost / float(total_cost) # (0..1)

            for progress_percent in current_step.handle():
                yield StepProgressResult(
                    current_step=current_step,
                    current_step_percent=progress_percent,
                    total_percent=completed_percent + total_normalized_current_cost * progress_percent
                )

            completed_percent += total_normalized_current_cost
            current_step = current_step.next_step


class ProcessStep(BaseStep):
    def handle(self):
        in_file = ffmpeg.input(str(self.context.in_file_path))
        probe = ffmpeg.probe(self.context.in_file_path)

        audio_streams = [stream for stream in probe['streams'] if stream.get('codec_type', 'N/A') == 'audio']
        nb_audio_streams = len(audio_streams)
        logger.debug(f'{nb_audio_streams=}')

        dest_path = MoviePathDestinationFinder(LegacyMovieFile(self.context.dest_filename), self.context.config).resolve_destination()
        dest_filepath = dest_path.joinpath(self.context.dest_filename)

        logger.info('Processing "%s" from "%s"...', dest_filepath, self.context.in_file_path)

        command = (
            ffmpeg
            .concat(
                *self.context.movie_segments.to_ffmpeg_concat_segments(in_file, audio_streams),
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
            logger.debug(f'{self.context.movie_segments.segments=}')
            logger.info('Running: %s', command.compile())

            total_seconds = self.context.movie_segments.total_seconds
            for item in ffmpeg_command_with_progress(command, cmd=['ffmpeg', '-hwaccel', 'cuda']):
                if item.get('time'):
                    processed_time = max(position_in_seconds(item['time']), 0)
                    yield processed_time / total_seconds

        except ffmpeg.Error as e:
            logger.exception(e.stderr)
            raise e

        return super().handle()


class BackupStep(BaseStep):
    def handle(self):
        logger.info('Backuping "%s"...', self.context.dest_filename)
        self.context.backup_policy_executor.execute(original_file_path=self.context.in_file_path)
        return super().handle()
