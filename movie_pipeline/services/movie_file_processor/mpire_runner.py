import logging
import webbrowser
from datetime import datetime
from pathlib import Path

from mpire import WorkerPool
from mpire.dashboard import start_dashboard

from settings import Settings
from util import progress_to_task_iterator

logger = logging.getLogger(__name__)


def noop(x):
    return x


class MovieFileProcessorMpireRunner:
    def __init__(self, folder_path: Path, edl_ext: str, config: Settings) -> None:
        self._folder_path = folder_path
        self._edl_ext = edl_ext
        self._config = config

        self._nb_worker = config.Processor.nb_worker if config.Processor else 1

        self._dashboard_details = start_dashboard()
        print(self._dashboard_details)

        webbrowser.open_new_tab(f"http://{self._dashboard_details['manager_host']}:{self._dashboard_details['dashboard_port_nr']}")

    def _prepare_processing(self):
        edls: list[Path] = []

        for edl in self._folder_path.glob(f'*{self._edl_ext}'):
            new_edl_name = edl.with_suffix(f'.pending_yml_{int(datetime.utcnow().timestamp())}')
            edl.rename(new_edl_name)
            edls.append(new_edl_name)

        return edls

    def _execute_processing(self, worker_id, edl: Path):
        import logging
        import logging.handlers

        from .core import MovieFileProcessor

        fh = logging.handlers.TimedRotatingFileHandler(filename=self._config.Logger.file_path if self._config.Logger else 'log.txt')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

        logging.basicConfig(level='INFO', handlers=(fh,))

        with WorkerPool(n_jobs=1, daemon=False, start_method='spawn', enable_insights=True) as p:
            movie_file_processor = MovieFileProcessor(edl_path=edl, config=self._config)
            iterable_len = 100

            try:
                p.map(
                    noop,
                    progress_to_task_iterator(movie_file_processor.process_with_progress(), count=iterable_len),
                    iterable_len=iterable_len,
                    progress_bar=True,
                    progress_bar_options={'desc': f'Processing {edl.stem}...', 'position': worker_id + 1}
                )
            except Exception as e:
                logger.exception(e)

        return edl

    def process_directory(self):
        logger.info('Processing: "%s"', self._folder_path)

        prepared_edls = [(path) for path in self._prepare_processing()]

        with WorkerPool(n_jobs=self._nb_worker, daemon=False, start_method='spawn', enable_insights=True, pass_worker_id=True) as pool:
            pool.map(self._execute_processing, prepared_edls, progress_bar=True)
