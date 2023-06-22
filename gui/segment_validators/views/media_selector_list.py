from typing import Any

import PySimpleGUI as sg

from ..controllers.media_selector_list_controller import (
    load_new_media, populate_media_selector,
    remove_validated_media_from_media_selector, toggle_media_selector_visibility)
from ..models.events import (APPLICATION_LOADED_EVENT,
                             MEDIA_SELECTOR_UPDATED_EVENT,
                             SEGMENTS_SAVED_EVENT,
                             TOGGLE_MEDIA_SELECTOR_VISIBILITY_EVENT)
from ..models.keys import MEDIA_SELECTOR_KEY


def layout():
    return [
        sg.Listbox(
            values=[],
            key=MEDIA_SELECTOR_KEY,
            enable_events=True,
            auto_size_text=False,
            horizontal_scroll=True,
            expand_x=True,
            expand_y=True
        )
    ]


handlers = {
    APPLICATION_LOADED_EVENT: populate_media_selector,
    MEDIA_SELECTOR_UPDATED_EVENT: load_new_media,
    TOGGLE_MEDIA_SELECTOR_VISIBILITY_EVENT: toggle_media_selector_visibility,
    SEGMENTS_SAVED_EVENT: remove_validated_media_from_media_selector
}


def handle_media_selector_list(window: sg.Window, event: str, values: dict[str, Any]):
    if event in handlers.keys():
        handlers[event](window, event, values)
