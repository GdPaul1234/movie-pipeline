from typing import Any, cast

import PySimpleGUI as sg

from util import seconds_to_position

from ..models.context import SegmentValidatorContext
from ..models.events import TASK_DONE_EVENT
from ..models.keys import SEGMENT_LIST_TABLE_KEY, VIDEO_DURATION_LABEL_KEY, VIDEO_POSITION_LABEL_KEY


def set_relative_position(window: sg.Window, event: str, _values: dict[str, Any]):
    metadata = cast(SegmentValidatorContext, window.metadata)
    player = metadata.media_player

    command, delta = event.split('::')
    window.perform_long_operation(lambda: getattr(
        player, command)(float(delta), window), TASK_DONE_EVENT)


def goto_selected_segment(window: sg.Window, event: str, _values: dict[str, Any]):
    metadata = cast(SegmentValidatorContext, window.metadata)
    table = cast(sg.Table, window[SEGMENT_LIST_TABLE_KEY])
    player = metadata.media_player

    segment_container = metadata.segment_container

    selected_segments = [segment_container.segments[row]
                         for row in table.SelectedRows]

    if len(selected_segments) != 1:
        return

    _, position = event.split('::')
    window.perform_long_operation(lambda: player.set_position(
        getattr(selected_segments[0], position), window), TASK_DONE_EVENT)


def set_video_information(window: sg.Window, _event: str, _values: dict[str, Any]):
    metadata = cast(SegmentValidatorContext, window.metadata)

    window[VIDEO_DURATION_LABEL_KEY].update(value=seconds_to_position(metadata.duration).split('.')[0])


def update_video_position(window: sg.Window, _event: str, _values: dict[str, Any]):
    metadata = cast(SegmentValidatorContext, window.metadata)
    window[VIDEO_POSITION_LABEL_KEY].update(value=seconds_to_position(metadata.position).split('.')[0])
