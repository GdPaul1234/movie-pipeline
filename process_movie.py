import concurrent.futures
import binpacking
import itertools
import logging
from pathlib import Path
from rich.live import Live
from rich.tree import Tree
from rich import print
from schema import Schema, Optional, Regex
from typing import cast
import yaml
import ffmpeg

from lib.backup_policy_executor import BackupPolicyExecutor, EdlFile
from lib.ui_factory import ProgressUIFactory, ProgressListener

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
    def __init__(self, edl_path: Path, config, *, backup_policy_executor = BackupPolicyExecutor) -> None:
        """
        Args:
            edl_path (Path): path to edit decision list file
                (naming: {movie file with suffix}.txt)
        """
        edl_content = yaml.safe_load(edl_path.read_text(encoding='utf-8'))
        edl_content = edl_content_schema.validate(edl_content)
        self._edl_file = EdlFile(edl_path, edl_content)

        self._backup_policy_executor = backup_policy_executor(self._edl_file, config)

        self._segments = []
        self._config = config

    @property
    def segments(self) -> list[tuple[float, float]]:
        if not len(self._segments):
            raw_segments: str = self._edl_file.content['segments']
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
        in_file_path = self._edl_file.path.with_suffix('')
        in_file = ffmpeg.input(str(in_file_path))
        probe = ffmpeg.probe(in_file_path)

        audio_streams = [stream for stream in probe['streams']
                         if stream.get('codec_type', 'N/A') == 'audio']
        nb_audio_streams = len(audio_streams)
        logger.debug(f'{nb_audio_streams=}')

        dest_filename = self._edl_file.content['filename']
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

            self._backup_policy_executor.execute(original_file_path=in_file_path)

            logger.info('"%s" processed sucessfully', dest_filepath)
        except ffmpeg.Error as e:
            logger.exception(e.stderr.decode())


class MovieFileProcessorFolderRunner:
    def __init__(self, folder_path: Path, edl_ext: str, progress_listener: ProgressListener, config) -> None:
        self._folder_path = folder_path
        self._edl_ext = edl_ext
        self._progress = progress_listener
        self._config = config

        self._nb_worker = self._config.getint('Processor', 'nb_worker', fallback=1)
        self._jobs_progresses = [ProgressUIFactory.create_job_progress() for _ in range(self._nb_worker)]

    def _distribute_fairly_edl(self):
        edls = list(self._folder_path.glob(f'*{self._edl_ext}'))

        if len(edls) == 0:
            return list(itertools.repeat([], times=self._nb_worker))

        return binpacking.to_constant_bin_number(
            edls,
            N_bin=self._nb_worker,
            key=lambda f: f.with_suffix('').stat().st_size
        )

    def _prepare_processing(self, tree_logger: Tree):
        for index, group in enumerate(self._distribute_fairly_edl()):
            subtree = tree_logger.add(f'Worker {index}')

            # rename distributed edls
            for edl in cast(list[Path], group):
                new_edl_name = edl.with_suffix(f'.pending_yml_{index}')
                edl.rename(new_edl_name)
                subtree.add(str(new_edl_name))

    def _execute_processing(self, worker_id: int, edl_ext: str):
        edls = list(self._folder_path.glob(f'*{edl_ext}'))
        job_progress = self._jobs_progresses[worker_id]
        task_id = job_progress.add_task(f'{edl_ext}...', total=len(edls))

        for edl in edls:
            MovieFileProcessor(edl, self._config).process()
            job_progress.advance(task_id)

    def process_directory(self):
        logger.info('Processing: "%s"', self._folder_path)

        tree = Tree("EDL to be processed")
        self._prepare_processing(tree_logger=tree)
        print(tree)

        with Live(self._progress.layout):
            self._progress.overall_progress.update(self._progress.overall_task, total=self._nb_worker)
            ProgressUIFactory.create_job_panel_row_from_job_progress(self._progress.layout, self._jobs_progresses)

            with concurrent.futures.ThreadPoolExecutor(max_workers=self._nb_worker) as executor:
                future_tasks = {
                    executor.submit(self._execute_processing, index, edl_ext): edl_ext
                    for index, edl_ext in map(lambda index: (index, f'.pending_yml_{index}'), range(self._nb_worker))
                }

                for future in concurrent.futures.as_completed(future_tasks):
                    edl_ext = future_tasks[future]
                    try:
                        future.result() # wait for completion
                    except Exception as e:
                        logger.error('Exception when processing *%s files: %s', edl_ext, e)
                        raise e
                    else:
                        self._progress.overall_progress.advance(self._progress.overall_task)
                        logger.info('Processed all %s edl files', edl_ext)

        logger.info('All movie files in "%s" processed', self._folder_path)


def command(options, config):
    logger.debug('args: %s', vars(options))

    filepath = Path(options.file)
    edl_ext: str = options.custom_ext


    progress_listener = ProgressUIFactory.create_process_listener()

    try:
        if filepath.is_file() and filepath.suffix == edl_ext:
            MovieFileProcessor(filepath, config).process()
        elif filepath.is_dir():
            MovieFileProcessorFolderRunner(filepath, edl_ext, progress_listener, config).process_directory()
        else:
            raise ValueError('Unknown file type')
    except Exception as e:
        logger.exception(e)
