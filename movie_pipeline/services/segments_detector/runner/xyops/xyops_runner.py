import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from pydantic import BaseModel
from pydantic.types import DirectoryPath, FilePath

from .....jobs.base_xyops_plugin import ReportedProgress
from .....lib.step_runner.step import BaseStep
from .....lib.util import total_movie_duration
from .....main import DetectorKey
from ...segments_detector import dump_segments_to_file, run_segment_detectors_with_progress
from .....settings import Settings

logger = logging.getLogger(__name__)


class Input(BaseModel):
    file_path: FilePath | DirectoryPath
    detector: str = DetectorKey.auto.name


@dataclass
class SegmentDetectorContext:
    movie_file_path: Path
    config: Settings
    detectors: list[DetectorKey] = field(default_factory=lambda: [DetectorKey.auto])


class SegmentDetectorStep(BaseStep[SegmentDetectorContext]):
    def _perform(self) -> Iterator[float]:
        selected_detectors_keys = [key.name for key in self.context.detectors]
        detect_progress = run_segment_detectors_with_progress(self.context.movie_file_path, selected_detectors_keys, self.context.config, raise_error=True)
        
        logger.info('Search segments in "%s"...', self.context.movie_file_path)

        try:
            while True:
                progress_percent = next(detect_progress)
                yield progress_percent
        except StopIteration as e:
            detectors_result = e.value
            dump_segments_to_file(detectors_result, movie_path=self.context.movie_file_path)


def detect_segments(input: Input, config: Settings) -> Iterator[ReportedProgress]:
    file_paths = [
        movie_path
        for metadata_path in input.file_path.glob('*.metadata.json')
        if not (movie_path := metadata_path.with_name(f"{metadata_path.name.removesuffix('.metadata.json')}")).with_suffix(f'{movie_path.suffix}.segments.json').exists()
    ] if input.file_path.is_dir() else [input.file_path]

    file_paths_size = len(file_paths)
    elapsed_times: dict[str, float] = {}

    for index, file_path in enumerate(file_paths):
        try:
            segment_detector = SegmentDetectorStep(
                context=SegmentDetectorContext(
                    movie_file_path=file_path,
                    detectors=[DetectorKey[input.detector]],
                    config=config
                ),
                description=f'{str(file_path)} segments detection',
                cost=total_movie_duration(file_path),
                next_step=None
            )

            for step_progress_result in segment_detector.process_all():
                elapsed_times[f'Item{index}'] = step_progress_result.current_step_elapsed_time
                
                yield {
                    'xy': 1,
                    'progress': round((index + step_progress_result.total_percent) / float(file_paths_size), 2), 
                    'perf': elapsed_times
                }

        except Exception as e:
            logger.exception(e)
