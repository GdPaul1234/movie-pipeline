from typing import Any
import PySimpleGUI as sg

from ..models.events import CONFIGURE_EVENT, SEGMENT_TIMELINE_UPDATED_EVENT, TIMELINE_POSTION_UPDATED_EVENT, SEGMENTS_UPDATED_EVENT, VIDEO_LOADED_EVENT, VIDEO_POSITION_UPDATED_EVENT
from ..models.keys import SEGMENT_TIMELINE_KEY
from ..models.context import TimelineContext
from ..controllers.segments_timeline_controller import draw_current_position_indicator, draw_segments, resize_timeline, update_current_position_indicator_position, update_selected_segment

GRAPH_SIZE = (480, 30)

right_click_menu = [
    '&Segments',
    [
        '&Add segment',
        '---',
        'Set &start',
        'Set &end'
    ]
]


def layout():
    return [
        sg.Graph(
            # Define the graph area
            canvas_size=GRAPH_SIZE, graph_bottom_left=(0., 0.), graph_top_right=(1., 1.),
            float_values=True,
            enable_events=True,  # mouse click events
            right_click_menu=right_click_menu,
            pad=0,
            background_color='#a6b2be',
            metadata=TimelineContext(),
            key=SEGMENT_TIMELINE_KEY
        )
    ]


handlers = {
    VIDEO_LOADED_EVENT: draw_current_position_indicator,
    CONFIGURE_EVENT: resize_timeline,
    SEGMENTS_UPDATED_EVENT: draw_segments,
    SEGMENT_TIMELINE_UPDATED_EVENT: update_selected_segment,
    TIMELINE_POSTION_UPDATED_EVENT: update_current_position_indicator_position,
    VIDEO_POSITION_UPDATED_EVENT: update_current_position_indicator_position
}


def handle_segments_timeline(window: sg.Window, event: str, values: dict[str, Any]):
    if event in handlers.keys():
        handlers[event](window, event, values)
