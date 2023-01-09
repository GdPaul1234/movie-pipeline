from typing import Any, cast
import PySimpleGUI as sg

from ..models.segment_container import SegmentContainer, Segment


right_click_menu = [
    '&Segments',
    [
        '&Delete segment(s)',
        '&Merge segments',
    ]
]


segments_list = [
    sg.Table(
        headings=(' Start ', '  End  ', 'Dur '),
        values=[('0:00:00', '0:00:00', '00:00')],
        right_click_menu=right_click_menu,
        enable_events=True,
        enable_click_events=True,
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
        player = window.metadata['media_player']
        current_position = player.get_time() / 1000
        segment_container.add(Segment(current_position, current_position + 1))
        render_values(window)

    elif event == 'Delete segment(s)':
        for selected_segment in selected_segments:
            segment_container.remove(selected_segment)
        render_values(window)

    elif event == 'Merge segments':
        segment_container.merge(selected_segments)
        render_values(window)
