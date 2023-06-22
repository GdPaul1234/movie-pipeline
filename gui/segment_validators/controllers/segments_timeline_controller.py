from typing import Any, cast

import PySimpleGUI as sg

from ..models.context import (SegmentValidatorContext, TimelineContext,
                              TimelineSegment)
from ..models.events import SEGMENT_TIMELINE_SELECTED_EVENT
from ..models.keys import SEGMENT_TIMELINE_KEY


def _get_position_in_percent(window: sg.Window):
    metadata = cast(SegmentValidatorContext, window.metadata)
    return metadata.position / metadata.duration


def draw_segments(window: sg.Window, _event = None, _values = None):
    metadata = cast(SegmentValidatorContext, window.metadata)
    graph = cast(sg.Graph, window[SEGMENT_TIMELINE_KEY])
    graph_metadata = cast(TimelineContext, graph.metadata)

    for segment in graph_metadata.segments:
        graph.delete_figure(segment.fid)
    graph_metadata.segments.clear()

    for segment in metadata.segment_container.segments:
        top_left = (segment.start / metadata.duration, 1.)
        bottom_right = (segment.end / metadata.duration, 0.)
        fill_color = '#f0f3f7' if segment in metadata.selected_segments else '#283b5b'

        rect = graph.draw_rectangle(top_left, bottom_right, fill_color=fill_color)
        graph.send_figure_to_back(rect)
        graph_metadata.segments.append(TimelineSegment(fid=rect, value=segment))


def draw_current_position_indicator(window: sg.Window, _event: str, _values: dict[str, Any]):
    graph = cast(sg.Graph, window[SEGMENT_TIMELINE_KEY])
    graph_metadata = cast(TimelineContext, graph.metadata)

    if graph_metadata.position_handle is None:
        position_handle = graph.draw_line((0., 0.), (0., 1.), color='red')
        graph_metadata.position_handle = position_handle
    else:
        resize_timeline(window, _event, _values)



def resize_timeline(window: sg.Window, _event: str, _values: dict[str, Any]):
    graph = cast(sg.Graph, window[SEGMENT_TIMELINE_KEY])
    graph_metadata = cast(TimelineContext, graph.metadata)

    graph.CanvasSize = graph.get_size()
    graph.relocate_figure(graph_metadata.position_handle, _get_position_in_percent(window), 0)
    draw_segments(window)
    window.refresh()


def update_selected_segment(window: sg.Window, _event: str, values: dict[str, Any]):
    metadata = cast(SegmentValidatorContext, window.metadata)
    graph = cast(sg.Graph, window[SEGMENT_TIMELINE_KEY])
    graph_metadata = cast(TimelineContext, graph.metadata)

    if len(figures := graph.get_figures_at_location(values[SEGMENT_TIMELINE_KEY])):
        selected_timeline_segment = next(
            (segment.value for segment in graph_metadata.segments if segment.fid == figures[0]),
            None
        )

        if selected_timeline_segment is not None:
            metadata.selected_segments = [selected_timeline_segment]
            window.write_event_value(SEGMENT_TIMELINE_SELECTED_EVENT, selected_timeline_segment)


def update_current_position_indicator_position(window: sg.Window, _event: str, _values: dict[str, Any]):
    graph = cast(sg.Graph, window[SEGMENT_TIMELINE_KEY])
    graph_metadata = cast(TimelineContext, graph.metadata)

    graph.relocate_figure(graph_metadata.position_handle, _get_position_in_percent(window), 0)
