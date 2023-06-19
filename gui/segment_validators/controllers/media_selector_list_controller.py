from pathlib import Path
from typing import Any, cast

import PySimpleGUI as sg
import yaml

from settings import Settings

from ..models.context import SegmentValidatorContext
from ..models.events import (APPLICATION_LOADED_EVENT, PREFILL_NAME_EVENT,
                             SEGMENT_IMPORTED_EVENT, VIDEO_LOADED_EVENT)
from ..models.keys import MEDIA_SELECTOR_KEY
from .edit_decision_file_dumper import ensure_decision_file_template


def init_metadata(window: sg.Window, filepath: Path, config: Settings):
    window.metadata = SegmentValidatorContext.init_context(filepath, config)

    window.write_event_value(VIDEO_LOADED_EVENT, True)
    window.write_event_value(SEGMENT_IMPORTED_EVENT, True)


def prefill_name(window: sg.Window, filepath: Path, config: Settings):
    if not ensure_decision_file_template(filepath, config):
        sg.popup_auto_close(f'Validated segments already exists for {filepath}', title='Aborting segments validation')

    template_path = filepath.with_suffix(f'{filepath.suffix}.yml.txt')
    template = yaml.safe_load(template_path.read_text(encoding='utf-8'))
    window.write_event_value(PREFILL_NAME_EVENT, template['filename'])


def populate_media_selector(window: sg.Window, _event: str, values: dict[str, Any]):
    selector = cast(sg.Combo, window[MEDIA_SELECTOR_KEY])

    media_paths, = values[APPLICATION_LOADED_EVENT]
    selector.update(values=media_paths)


def load_new_media(window: sg.Window, _event: str, values: dict[str, Any]):
    metadata = cast(SegmentValidatorContext, window.metadata)
    filename = cast(Path, values[MEDIA_SELECTOR_KEY][0])

    if filename.is_file():
        init_metadata(window, filename, metadata.config)
        prefill_name(window, filename, metadata.config)

