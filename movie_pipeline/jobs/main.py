import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from ..jobs.base_cronicle_plugin import BaseCroniclePlugin, BaseCroniclePluginInput
from ..settings import Settings

default_config_path = Path.home() / '.movie_pipeline' / 'config.env'


logging.basicConfig(level='INFO', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_job_config(config_path=default_config_path) -> Settings:
    os.chdir(config_path.parent)
    return Settings(_env_file=config_path, _env_file_encoding='utf-8') # type: ignore


def archive_movies(config_path=default_config_path, raw_inputs: Optional[str] = None):
    from ..services.movie_archiver.runner.cronicle_runner import Input, archive_movies
    raw_inputs = raw_inputs or next(sys.stdin)

    BaseCroniclePlugin(
        lambda params: archive_movies(params, get_job_config(config_path)),
        inputs=BaseCroniclePluginInput[Input](**json.loads(raw_inputs))
    ).run()


def detect_segments(config_path=default_config_path, raw_inputs: Optional[str] = None):
    from ..services.segments_detector.runner.cronicle.cronicle_runner import Input, detect_segments
    raw_inputs = raw_inputs or next(sys.stdin)

    BaseCroniclePlugin(
        lambda params: detect_segments(params, get_job_config(config_path)),
        inputs=BaseCroniclePluginInput[Input](**json.loads(raw_inputs))
    ).run()


def process_movie(config_path=default_config_path, raw_inputs: Optional[str] = None):
    from ..services.movie_file_processor.runner.cronicle.cronicle_runner import FileInput, process_file
    raw_inputs = raw_inputs or next(sys.stdin)

    BaseCroniclePlugin(
        lambda params: process_file(params, get_job_config(config_path)),
        inputs=BaseCroniclePluginInput[FileInput](**json.loads(raw_inputs))
    ).run()


def process_directory(config_path=default_config_path, raw_inputs: Optional[str] = None):
    from ..services.movie_file_processor.runner.cronicle.cronicle_runner import DirectoryInput, process_directory
    raw_inputs = raw_inputs or next(sys.stdin)

    BaseCroniclePlugin(
        lambda params: process_directory(params, get_job_config(config_path)),
        inputs=BaseCroniclePluginInput[DirectoryInput](**json.loads(raw_inputs))
    ).run()
