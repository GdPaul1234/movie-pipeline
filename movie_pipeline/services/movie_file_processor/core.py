import logging
from collections import deque
from pathlib import Path

import yaml
from rich.progress import Progress
from schema import Optional, Regex, Schema

from ...lib.backup_policy_executor import BackupPolicyExecutor, EdlFile
from ...models.movie_segments import MovieSegments
from ...settings import Settings
from .movie_file_processor_step import BackupStep, MovieFileProcessorContext, ProcessStep
from .rich_all_steps_interactive_progress_display import process_with_progress_tui

logger = logging.getLogger(__name__)


edl_content_schema = Schema({
    # valid filename of the output file with .mp4 suffix
    "filename": Regex(r"^[\w&àéèï'!()\[\], #-.]+\.mp4$"),
    # format: hh:mm:ss.ss-hh:mm:ss.ss,hh-mm:ss…
    "segments": Regex(r'(?:(?:\d{2}:\d{2}:\d{2}\.\d{2,3})-(?:\d{2}:\d{2}:\d{2}\.\d{2,3}),)+'),
    Optional("skip_backup", default=False): bool
})


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

        context = MovieFileProcessorContext(
            backup_policy_executor=backup_policy_executor(edl_file, config),
            movie_segments=MovieSegments(raw_segments=edl_file.content['segments']),
            config=config,
            in_file_path=edl_file.path.with_suffix(''),
            dest_filename=edl_file.content['filename']
        )

        self.movie_segments = context.movie_segments
        self.segments = context.movie_segments.segments
        self.dest_filename = context.dest_filename

        self._movie_file_processor_root_step = ProcessStep(
            context=context,
            description=self.dest_filename,
            cost=0.8,
            next_step=BackupStep(
                context=context,
                description=f'Backuping {self.dest_filename}...',
                cost=0.2,
                next_step=None
            )
        )

    def process(self):
        deque(self.process_with_progress(), maxlen=0)

    def process_with_progress(self):
        logger.info(self.dest_filename)

        for step_progress_result in self._movie_file_processor_root_step.process_all():
            yield step_progress_result.total_percent

        logger.info('"%s" processed successfully', self.dest_filename)

    def process_with_progress_tui(self, progress: Progress):
        for progress_percent in process_with_progress_tui(progress, self._movie_file_processor_root_step):
            yield progress_percent

        logger.info('"%s" processed successfully', self.dest_filename)
