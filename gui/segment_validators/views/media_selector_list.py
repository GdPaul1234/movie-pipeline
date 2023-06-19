import PySimpleGUI as sg
from typing import Any

from ..models.events import APPLICATION_LOADED_EVENT, MEDIA_SELECTOR_UPDATED_EVENT
from ..models.keys import MEDIA_SELECTOR_KEY
from ..controllers.media_selector_list_controller import load_new_media, populate_media_selector


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
    MEDIA_SELECTOR_UPDATED_EVENT: load_new_media
}


def handle_media_selector_list(window: sg.Window, event: str, values: dict[str, Any]):
    if event in handlers.keys():
        handlers[event](window, event, values)
