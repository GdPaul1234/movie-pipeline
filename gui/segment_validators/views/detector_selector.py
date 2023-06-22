from typing import Any
import PySimpleGUI as sg


from ..controllers.detector_selector_controller import populate_detector_selector, import_segments_from_selected_detector
from ..models.events import SEGMENT_IMPORTED_EVENT, SELECTED_DETECTOR_UPDATED_EVENT
from ..models.keys import DETECTOR_SELECTOR_KEY

handlers = {
    SEGMENT_IMPORTED_EVENT: populate_detector_selector,
    SELECTED_DETECTOR_UPDATED_EVENT: import_segments_from_selected_detector
}


def layout():
    return [
        sg.Combo(
            [],
            enable_events=True,
            expand_x=True,
            pad=((0, 0), (5, 5)),
            key=DETECTOR_SELECTOR_KEY
        )
    ]


def handle_detector(window: sg.Window, event: str, values: dict[str, Any]):
    if event in handlers.keys():
        handlers[event](window, event, values)
