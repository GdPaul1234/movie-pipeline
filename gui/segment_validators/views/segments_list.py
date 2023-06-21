from typing import Any
import PySimpleGUI as sg

from ..models.keys import SEGMENT_LIST_TABLE_KEY
from ..models.events import SEGMENT_ADD_EVENT, SEGMENT_DELETE_EVENT, SEGMENT_MERGE_EVENT, SEGMENT_LIST_UPDATED_EVENT, SEGMENT_SET_START_EVENT, SEGMENT_SET_END_EVENT, SEGMENT_TIMELINE_SELECTED_EVENT, SEGMENTS_VALIDATED_EVENT
from ..controllers.segments_list_controller import _render_values, add_segment, delete_segments, edit_segment, merge_segments, focus_timeline_selected_segment, forward_updated_event, validate_segments

render_values = _render_values


right_click_menu = [
    '&Segments',
    [
        '&Merge segments',
        '&Delete segment(s)',
    ]
]


def layout():
    return [
        sg.Table(
            headings=('Start', 'End', 'Dur'),
            values=[('00:00:00.00', '00:00:00.00', '00:00')],
            right_click_menu=right_click_menu,
            enable_events=True,
            enable_click_events=True,
            auto_size_columns=True,
            expand_x=True,
            expand_y=True,
            pad=0,
            key=SEGMENT_LIST_TABLE_KEY
        )
    ]


handlers = {
    SEGMENT_ADD_EVENT: add_segment,
    SEGMENT_DELETE_EVENT: delete_segments,
    SEGMENT_MERGE_EVENT: merge_segments,
    SEGMENT_LIST_UPDATED_EVENT: forward_updated_event,
    SEGMENT_TIMELINE_SELECTED_EVENT: focus_timeline_selected_segment,
    SEGMENT_SET_START_EVENT: edit_segment,
    SEGMENT_SET_END_EVENT: edit_segment,
    SEGMENTS_VALIDATED_EVENT: validate_segments
}


def handle_segments_list(window: sg.Window, event: str, values: dict[str, Any]):
    if event in handlers.keys():
        handlers[event](window, event, values)
