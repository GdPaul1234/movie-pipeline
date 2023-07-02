import logging
import os
import subprocess
import threading
import time
import requests
import sys
import textwrap
import webbrowser
from pathlib import Path

from settings import Settings

logger = logging.getLogger(__name__)

url = 'http://localhost:3000/d/ddac5331-26b2-4e4d-88f4-b0fbc3067306/media-stats'
cwd = Path(__file__).parent.parent.joinpath('templates', 'grafana')
required_plugins = {'frser-sqlite-datasource'}


def health_check():
    for _ in range(10):
        logger.info('Wait for the dashboard to be available...')

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            webbrowser.open_new_tab(url)
            return

        except (requests.ConnectionError, requests.Timeout):
            pass

        time.sleep(5)

    logger.error('Fail to open dashboard. Please check if docker is running...')


def run_helth_check():
    thread = threading.Thread(target=health_check, daemon=True)
    thread.start()
    return thread


def command(options, config: Settings):
    if config.MediaDatabase is None or not config.MediaDatabase.db_path.is_file():
        raise ValueError('Missing or invalid db_path in config')

    if not (plugin_dir := cwd.joinpath('grafana_config', 'tmp', 'plugins')).is_dir():
        raise RuntimeError(textwrap.dedent(f'''
            Grafana plugins are missing!
            Download {required_plugins} and unzip it inside "{str(plugin_dir)}"
        '''))

    logger.info('Launching grafana...')
    logger.info('Kill this terminal to terminate')

    logger.info(textwrap.dedent(f'''
        Once ready, the dashboard is available at:
        {url}
    '''))

    run_helth_check()

    try:
        env = os.environ.copy()
        env['MOVIE_PIPELINE_MEDIA_DB_PATH'] = str(config.MediaDatabase.db_path)

        subprocess.run(
            [
                'docker',
                'compose',
                '-p', 'movie_pipeline_grafana_media_dashboard',
                'up'
            ],
            cwd=cwd, env=env,
            stderr=sys.stderr, stdout=sys.stdout,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as error:
        logger.error(error.stderr)
        raise error
