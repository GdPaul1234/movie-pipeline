from pathlib import Path
from typing import Any, Literal, cast
import PySimpleGUI as sg

from ..controllers.edit_decision_file_dumper import EditDecisionFileDumper
from ..models.segment_container import SegmentContainer, Segment


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
            expand_y=True,
            pad=0,
            key='-SEGMENTS-LIST-'
        )
    ]


def render_values(window: sg.Window):
    segments = cast(tuple[Segment], window.metadata['segment_container'].segments)

    def render(segment: Segment):
        return repr(segment).split(',')

    values = [render(segment) for segment in segments]
    window['-SEGMENTS-LIST-'].update(values=values)
    window.write_event_value('-SEGMENTS-UPDATED-', True)


def edit_segments(window: sg.Window, event: Literal['Set start', 'Set end'], values: dict[str, Any]):
    segment_container = cast(SegmentContainer, window.metadata['segment_container'])
    table = cast(sg.Table, window['-SEGMENTS-LIST-'])
    selected_segments = [segment_container.segments[row] for row in table.SelectedRows]

    if len(selected_segments) != 1: return

    current_position = window.metadata['position_ms'] / 1000

    try:
        edited_segment = Segment(current_position, selected_segments[0].end) if event == 'Set start' \
            else Segment(selected_segments[0].start, current_position)
    except ValueError as e:
        sg.popup_error(e)
    else:
        segment_container.edit(selected_segments[0], edited_segment)
        render_values(window)


def write_segments(window: sg.Window, values: dict[str, Any]) -> Path|None:
    segment_container = cast(SegmentContainer, window.metadata['segment_container'])
    dumper = EditDecisionFileDumper(
        title=values['-NAME-'],
        source_path=window.metadata['filepath'],
        segment_container=segment_container,
        config=window.metadata['config']
    )

    return dumper.dump_decision_file()


def handle_segments_list(window: sg.Window, event: str, values: dict[str, Any]):
    segment_container = cast(SegmentContainer, window.metadata['segment_container'])
    table = cast(sg.Table, window['-SEGMENTS-LIST-'])

    selected_segments = [segment_container.segments[row] for row in table.SelectedRows]

    if event == '-SEGMENTS-LIST-':
        window.metadata['selected_segments'] = selected_segments
        window.write_event_value('-SEGMENTS-UPDATED-', True)

    elif event == '-SEGMENT-TIMELINE-SELECTED-':
        if  (row := next(
            (idx for idx, value in enumerate(table.Values)
             if ','.join(value) == repr(values['-SEGMENT-TIMELINE-SELECTED-'])),
            None
        )) is not None:
            tree = table.TKTreeview
            child_id = tree.get_children()[row]
            tree.focus(child_id)
            tree.selection_set(child_id)

    elif event == 'Add segment':
        current_position = window.metadata['position_ms'] / 1000
        segment_container.add(Segment(current_position, current_position + 1))
        render_values(window)

    elif event == 'Delete segment(s)':
        for selected_segment in selected_segments:
            segment_container.remove(selected_segment)
        render_values(window)

    elif event == 'Merge segments':
        if len(selected_segments) >= 2:
            segment_container.merge(selected_segments)
            render_values(window)

    elif event in ('Set start', 'Set end'):
        edit_segments(window, event, values)

    elif event == 'Validate and quit':
        if edl_path := write_segments(window, values):
            sg.popup_auto_close(edl_path, title='Segments saved')
            window.write_event_value(sg.WIN_CLOSED, True)
        else:
            sg.popup_auto_close(title='Segments not saved, an error has occured')
