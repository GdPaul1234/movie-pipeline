from dataclasses import astuple
from typing import Any, cast
import PySimpleGUI as sg

from ..models.segment_container import SegmentContainer, Segment
from util import seconds_to_position


right_click_menu = [
    '&Segments',
    [
        '&Delete segment',
        '&Merge segments',
    ]
]


segments_list = [
    sg.Table(
        headings=(' Start ', '  End  ', 'Dur '),
        values=[('0:00:00', '0:00:00', '00:00')],
        right_click_menu=right_click_menu,
        enable_click_events=True,
        expand_y=True,
        pad=0,
        key='-SEGMENTS-LIST-'
    )
]


def render_values(window: sg.Window):
    segments = cast(tuple[Segment], window.metadata['segments'].segments)

    def render(segment: Segment):
        start, end = astuple(segment)
        return (
            seconds_to_position(start),
            seconds_to_position(end),
            "{:02.0f}:{:02.0f}".format(*divmod(segment.duration, 60))
        )

    values = [render(segment) for segment in segments]
    window['-SEGMENTS-LIST-'].update(values=values)


def get_selected_segment(window: sg.Window) -> Segment|None:
    segment_container = cast(SegmentContainer, window.metadata['segments'])
    table = cast(sg.Table, window['-SEGMENTS-LIST-'])
    row, _ = table.get_last_clicked_position()

    if row is None or row == -1: return
    if row >= len(segment_container.segments): return

    return segment_container.segments[row]



def handle_segments_list(window: sg.Window, event: str, values: dict[str, Any]):
    segment_container = cast(SegmentContainer, window.metadata['segments'])

    if event == 'Add segment':
        player = window.metadata['media_player']
        current_position = player.get_time() / 1000
        segment_container.add(Segment(current_position, current_position + 1))
        render_values(window)

    elif event == 'Delete segment' and (selected_segment := get_selected_segment(window)):
        segment_container.remove(selected_segment)
        render_values(window)

    elif event == 'Merge segments':
        render_values(window)
