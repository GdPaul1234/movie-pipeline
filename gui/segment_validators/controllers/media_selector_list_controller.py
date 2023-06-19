from pathlib import Path
from typing import Any, cast

import PySimpleGUI as sg
import yaml

from settings import Settings

from ..models.context import SegmentValidatorContext
from ..models.events import (APPLICATION_LOADED_EVENT, PREFILL_NAME_EVENT,
                             SEGMENT_IMPORTED_EVENT, VIDEO_LOADED_EVENT)
from ..models.keys import (FLASH_TOP_NOTICE_KEY, MEDIA_SELECTOR_CONTAINER_KEY,
                           MEDIA_SELECTOR_KEY,
                           TOGGLE_MEDIA_SELECTOR_VISIBILITY_KEY)
from ..views.texts import TEXTS

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
    flash_notice_label = cast(sg.Text, window[FLASH_TOP_NOTICE_KEY])
    metadata = cast(SegmentValidatorContext | None, window.metadata)
    filename = cast(Path, values[MEDIA_SELECTOR_KEY][0])

    flash_notice_label.update(value=TEXTS['loading_media'])
    window.refresh()

    if filename.is_file():
        config = metadata.config if metadata else values['config']
        init_metadata(window, filename, config)
        prefill_name(window, filename, config)

    flash_notice_label.update(value=TEXTS['review_segments_description'])
    window.set_title(f'Segments Reviewer - {str(filename)}')
    window.refresh()


def toggle_media_selector_visibility(window: sg.Window, _event: str, _values: dict[str, Any]):
    media_selector_container = cast(sg.Frame, window[MEDIA_SELECTOR_CONTAINER_KEY])
    toggle_media_selector_button = cast(sg.Button, window[TOGGLE_MEDIA_SELECTOR_VISIBILITY_KEY])

    media_selector_container_visibility = not media_selector_container.visible
    toggle_media_selector_button.update(text='<<' if media_selector_container_visibility else '>>')
    media_selector_container.update(visible=media_selector_container_visibility)
