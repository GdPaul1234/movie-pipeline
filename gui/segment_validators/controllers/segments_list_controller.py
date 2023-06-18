from pathlib import Path
from tkinter import ttk
from typing import Any, cast

import PySimpleGUI as sg

from ..controllers.edit_decision_file_dumper import EditDecisionFileDumper
from ..models.context import SegmentValidatorContext
from ..models.events import (SEGMENT_SET_START_EVENT,
                             SEGMENT_TIMELINE_SELECTED_EVENT,
                             SEGMENTS_UPDATED_EVENT)
from ..models.keys import SEGMENT_LIST_TABLE_KEY
from ..models.segment_container import Segment


def _get_selected_segments(window: sg.Window):
    metadata = cast(SegmentValidatorContext, window.metadata)
    table = cast(sg.Table, window[SEGMENT_LIST_TABLE_KEY])

    return [metadata.segment_container.segments[row] for row in table.SelectedRows]


def _render_values(window: sg.Window):
    metadata = cast(SegmentValidatorContext, window.metadata)
    segments = metadata.segment_container.segments

    def render(segment: Segment):
        return repr(segment).split(',')

    values = [render(segment) for segment in segments]
    window[SEGMENT_LIST_TABLE_KEY].update(values=values)
    window.write_event_value(SEGMENTS_UPDATED_EVENT, True)


def _write_segments(window: sg.Window, values: dict[str, Any]) -> Path|None:
    metadata = cast(SegmentValidatorContext, window.metadata)

    dumper = EditDecisionFileDumper(
        title=values['-NAME-'],
        source_path=metadata.filepath,
        segment_container=metadata.segment_container,
        config=metadata.config
    )

    return dumper.dump_decision_file()


def forward_updated_event(window: sg.Window, _event: str, _values: dict[str, Any]):
    metadata = cast(SegmentValidatorContext, window.metadata)

    metadata.selected_segments = _get_selected_segments(window)
    window.write_event_value(SEGMENTS_UPDATED_EVENT, True)


def focus_timeline_selected_segment(window: sg.Window, _event: str, values: dict[str, Any]):
    table = cast(sg.Table, window[SEGMENT_LIST_TABLE_KEY])

    if  (row := next(
            (idx for idx, value in enumerate(table.Values)
             if ','.join(value) == repr(values[SEGMENT_TIMELINE_SELECTED_EVENT])),
            None
        )) is not None:
            tree = cast(ttk.Treeview, table.TKTreeview)
            child_id = tree.get_children()[row]
            tree.focus(child_id)
            tree.selection_set(child_id)


def add_segment(window: sg.Window, _event: str, _values: dict[str, Any]):
    metadata = cast(SegmentValidatorContext, window.metadata)

    metadata.segment_container.add(Segment(metadata.position, metadata.position + 1))
    _render_values(window)


def delete_segments(window: sg.Window, _event: str, _values: dict[str, Any]):
    metadata = cast(SegmentValidatorContext, window.metadata)

    for selected_segment in metadata.selected_segments:
        metadata.segment_container.remove(selected_segment)

    _render_values(window)


def merge_segments(window: sg.Window, _event: str, _values: dict[str, Any]):
    metadata = cast(SegmentValidatorContext, window.metadata)

    if len(metadata.selected_segments) >= 2:
        metadata.segment_container.merge(metadata.selected_segments)
        _render_values(window)


def edit_segment(window: sg.Window, event: str, _values: dict[str, Any]):
    metadata = cast(SegmentValidatorContext, window.metadata)

    if len(metadata.selected_segments) != 1: return

    try:
        edited_segment = Segment(metadata.position, metadata.selected_segments[0].end) if event == SEGMENT_SET_START_EVENT \
            else Segment(metadata.selected_segments[0].start, metadata.position)
    except ValueError as e:
        sg.popup_error(e)
    else:
        metadata.segment_container.edit(metadata.selected_segments[0], edited_segment)
        _render_values(window)


def validate_segments(window: sg.Window, _event: str, values: dict[str, Any]):
    if edl_path := _write_segments(window, values):
        sg.popup_auto_close(edl_path, title='Segments saved')
        window.write_event_value(sg.WIN_CLOSED, True)
    else:
        sg.popup_auto_close(title='Segments not saved, an error has occured')
