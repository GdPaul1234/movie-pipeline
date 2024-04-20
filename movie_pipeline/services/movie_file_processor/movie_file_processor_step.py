import logging
import math
import shutil
import time
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional, cast

import ffmpeg
from deffcode import Sourcer

from ...lib.backup_policy_executor import BackupPolicyExecutor, EdlFile
from ...lib.ffmpeg.ffmpeg_cli_presets import get_ffencode_audio_params, get_ffencode_video_params, get_ffprefixes
from ...lib.ffmpeg.ffmpeg_with_progress import ffmpeg_command_with_progress
from ...lib.movie_path_destination_finder import MoviePathDestinationFinder
from ...lib.util import position_in_seconds
from ...models.movie_file import LegacyMovieFile
from ...models.movie_segments import MovieSegments
from ...settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class StepProgressResult:
    current_step: 'BaseStep'
    current_step_percent: float
    current_step_elapsed_time: float
    total_percent: float


@dataclass
class MovieFileProcessorContext:
    edl_file: EdlFile
    backup_policy_executor: BackupPolicyExecutor
    movie_segments: MovieSegments
    config: Settings
    in_file_path: Path
    dest_filename: str

    def validate_dest_file(self, dest_path: Path, config: Settings):
        try:
            dest_filepath = dest_path / self.dest_filename
            sourcer = Sourcer(str(dest_filepath), custom_ffmpeg=str(config.ffmpeg_path)).probe_stream()
            video_metadata = cast(dict[str, Any], sourcer.retrieve_metadata())
            return math.isclose(video_metadata['source_duration_sec'], self.movie_segments.total_seconds, abs_tol=1)

        except ValueError:
            return False


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

    def _before_perform(self) -> None:
        pass

    def _perform(self) -> Iterator[float]:
        ...

    def _after_perform(self) -> None:
        pass

    def handle(self) -> Iterator[tuple[float, float]]:
        start_time = time.perf_counter()
        self._before_perform()

        for progress_percent in self._perform():
            yield progress_percent, time.perf_counter() - start_time

        self._after_perform()
        yield 1, time.perf_counter() - start_time

    def process_all(self) -> Iterator[StepProgressResult]:
        total_cost = self.total_cost

        completed_percent = 0.0
        current_step = self

        while current_step is not None:
            total_normalized_current_cost = current_step.cost / float(total_cost) # (0..1)

            for progress_percent, progress_elapsed_time in current_step.handle():
                yield StepProgressResult(
                    current_step=current_step,
                    current_step_percent=progress_percent,
                    current_step_elapsed_time=progress_elapsed_time,
                    total_percent=completed_percent + total_normalized_current_cost * progress_percent
                )

            completed_percent += total_normalized_current_cost
            current_step = current_step.next_step


class BaseStepError(Exception):
    pass


class BaseStepInterruptedError(Exception):
    pass


class ProcessStep(BaseStep):
    def _before_perform(self) -> None:
        self._in_file = ffmpeg.input(str(self.context.in_file_path))
        self._dest_path = MoviePathDestinationFinder(LegacyMovieFile(self.context.dest_filename), self.context.config).resolve_destination()
        self._dest_filepath = self._dest_path / self.context.dest_filename

        if self._dest_path.is_dir() and not any(self._dest_path.iterdir()):
            return

        if self._dest_filepath.is_file():
            if self.context.validate_dest_file(self._dest_path, self.context.config):
                self.context.edl_file.path.rename(self.context.edl_file.path.with_suffix('.yml.done'))
                raise BaseStepInterruptedError('Valid "%s" already exists', self.context.dest_filename)
            else:
                logger.info('"%s" does not conform to processing decision file, deleting it...', self._dest_filepath)
                self._dest_filepath.unlink()

        if not LegacyMovieFile(self.context.dest_filename).is_serie:
            logger.info('"%s" is not empty, recreating it it...', self._dest_path)
            shutil.rmtree(self._dest_path)
            self._dest_path.mkdir(parents=True)

    def _perform(self) -> Iterator[float]:
        logger.info('Processing "%s" from "%s"...', self._dest_filepath, self.context.in_file_path)

        probe = ffmpeg.probe(self.context.in_file_path)
        self._audio_streams = [stream for stream in probe['streams'] if stream.get('codec_type', 'N/A') == 'audio']
        self._nb_audio_streams = len(self._audio_streams)
        logger.debug(f'{self._nb_audio_streams=}')

        command = (
            ffmpeg
            .concat(
                *self.context.movie_segments.to_ffmpeg_concat_segments(self._in_file, self._audio_streams),
                v=1, a=self._nb_audio_streams
            )
            .output(
                str(self._dest_filepath),
                **get_ffencode_video_params(self.context.config.ffmpeg_hwaccel),
                **get_ffencode_audio_params(),
                **{f'map_metadata:s:a:{index}': f'0:s:a:{index}' for index in range(self._nb_audio_streams)},
                dn=None, sn=None, ignore_unknown=None,
            )
        )

        try:
            logger.debug(f'{self.context.movie_segments.segments=}')
            logger.info('Running: %s', command.compile())

            total_seconds = self.context.movie_segments.total_seconds
            for item in ffmpeg_command_with_progress(command, cmd=['ffmpeg', *get_ffprefixes(self.context.config.ffmpeg_hwaccel)]):
                if item.get('time'):
                    processed_time = max(position_in_seconds(item['time']), 0)
                    yield processed_time / total_seconds

        except ffmpeg.Error as e:
            logger.exception(e.stderr)
            raise e

    def _after_perform(self) -> None:
        if not self.context.validate_dest_file(self._dest_path, self.context.config):
            raise BaseStepError(f'"{self._dest_filepath}" does not conform to processing decision file')


class BackupStep(BaseStep):
    def _perform(self) -> Iterator[float]:
        logger.info('Backuping "%s"...', self.context.dest_filename)
        self.context.backup_policy_executor.execute(original_file_path=self.context.in_file_path)
        yield 1
