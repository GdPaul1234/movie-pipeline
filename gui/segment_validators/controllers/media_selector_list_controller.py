from pathlib import Path
from typing import Any, cast

import PySimpleGUI as sg
import yaml

from settings import Settings

from ..models.context import SegmentValidatorContext
from ..models.events import (APPLICATION_LOADED_EVENT,
                             MEDIA_SELECTOR_UPDATED_EVENT, PREFILL_NAME_EVENT,
                             SEGMENT_IMPORTED_EVENT, SEGMENTS_SAVED_EVENT,
                             VIDEO_LOADED_EVENT)
from ..models.keys import (FLASH_TOP_NOTICE_KEY, MEDIA_SELECTOR_CONTAINER_KEY,
                           MEDIA_SELECTOR_KEY,
                           TOGGLE_MEDIA_SELECTOR_VISIBILITY_KEY)
from ..views.texts import TEXTS
from .edit_decision_file_dumper import ensure_decision_file_template
from .import_segments_from_file import prepend_last_segments_to_segment_file


def init_metadata(window: sg.Window, filepath: Path, config: Settings):
    window.metadata = SegmentValidatorContext.init_context(filepath, config)

    window.write_event_value(VIDEO_LOADED_EVENT, True)
    window.write_event_value(SEGMENT_IMPORTED_EVENT, True)


def prefill_name(window: sg.Window, filepath: Path, config: Settings):
    if not ensure_decision_file_template(filepath, config):
        sg.popup_auto_close(f'Validated segments already exists for {filepath}', title='Aborting segments validation')
        window.write_event_value(SEGMENTS_SAVED_EVENT, True)

    else:
        template_path = filepath.with_suffix(f'{filepath.suffix}.yml.txt')
        template = yaml.safe_load(template_path.read_text(encoding='utf-8'))
        window.write_event_value(PREFILL_NAME_EVENT, template['filename'])


def populate_media_selector(window: sg.Window, _event: str, values: dict[str, Any]):
    selector = cast(sg.Listbox, window[MEDIA_SELECTOR_KEY])

    media_paths, = values[APPLICATION_LOADED_EVENT]
    selector.update(values=media_paths, set_to_index=0)


def load_new_media(window: sg.Window, _event: str, values: dict[str, Any]):
    flash_notice_label = cast(sg.Text, window[FLASH_TOP_NOTICE_KEY])
    selector = cast(sg.Listbox, window[MEDIA_SELECTOR_KEY])
    metadata = cast(SegmentValidatorContext | None, window.metadata)
    filepath = cast(Path, values[MEDIA_SELECTOR_KEY][0])

    if metadata is not None:
        old_filepath = metadata.filepath
        old_segments =metadata.segment_container
        prepend_last_segments_to_segment_file(old_filepath, old_segments)

    flash_notice_label.update(value=TEXTS['loading_media'])
    window.refresh()

    if filepath.is_file():
        config = metadata.config if metadata else values['config']
        init_metadata(window, filepath, config)
        prefill_name(window, filepath, config)

    flash_notice_label.update(value=TEXTS['review_segments_description'])
    window.set_title(f'Segments Reviewer - {str(filepath)}')
    selector.set_value(filepath)
    window.refresh()


def toggle_media_selector_visibility(window: sg.Window, _event: str, _values: dict[str, Any]):
    media_selector_container = cast(sg.Frame, window[MEDIA_SELECTOR_CONTAINER_KEY])
    toggle_media_selector_button = cast(sg.Button, window[TOGGLE_MEDIA_SELECTOR_VISIBILITY_KEY])

    media_selector_container_visibility = not media_selector_container.visible
    toggle_media_selector_button.update(text='<<' if media_selector_container_visibility else '>>')
    media_selector_container.update(visible=media_selector_container_visibility)


def remove_validated_media_from_media_selector(window: sg.Window, _event: str, _values: dict[str, Any]):
    selector = cast(sg.Listbox, window[MEDIA_SELECTOR_KEY])
    metadata = cast(SegmentValidatorContext, window.metadata)

    medias: list[Path] = selector.get_list_values()
    next_media = medias[(medias.index(metadata.filepath) + 1) % len(medias)]

    updated_medias = [media for media in medias if media != metadata.filepath]
    selector.update(values=updated_medias)

    window.write_event_value(MEDIA_SELECTOR_UPDATED_EVENT, [next_media])

