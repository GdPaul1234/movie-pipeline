from typing import Any, cast
import PySimpleGUI as sg

from gui.segment_validators.lib.simple_video_only_player import SimpleVideoOnlyPlayerConsumer
from gui.segment_validators.models.segment_container import SegmentContainer

from util import seconds_to_position

def btn(text, /, *, key=None, size=(6,1), pad=(1,1)):
    return sg.Button(text, key=(key or text), size=size, pad=pad)


def txt(text, key):
    return sg.Column([[sg.Text(text, key=key, pad=0)]], pad=0)


def layout():
    return [
        txt('00:00:00', key='-VIDEO-POSITION-'),
        sg.Push(),
        btn('>[-', key='goto_selected_segment::start', size=(3,1)),
        btn('-]<', key='goto_selected_segment::end', size=(3,1)),
        sg.Sizer(5),
        btn('-1s', key='set_relative_position::-1', size=(3,1)),
        btn('+1s', key='set_relative_position::1', size=(3,1)),
        sg.Sizer(5),
        btn('-5s', key='set_relative_position::-5', size=(3,1)),
        btn('+5s', key='set_relative_position::5', size=(3,1)),
        sg.Sizer(5),
        btn('-15s', key='set_relative_position::-15', size=(4,1)),
        btn('+15s', key='set_relative_position::15', size=(4,1)),
        sg.Push(),
        txt('00:00:00', key='-VIDEO-DURATION-'),
    ]


def handle_media_control(window: sg.Window, event: str, values: dict[str, Any]):
    player = cast(SimpleVideoOnlyPlayerConsumer, window.metadata['media_player'])

    if isinstance(event, str) and event.startswith('set_relative_position::'):
        command, delta = event.split('::')
        window.perform_long_operation(lambda: getattr(player, command)(float(delta), window), '-TASK-DONE-')

    elif isinstance(event, str) and event.startswith('goto_selected_segment::'):
        segment_container = cast(SegmentContainer, window.metadata['segment_container'])
        table = cast(sg.Table, window['-SEGMENTS-LIST-'])
        selected_segments = [segment_container.segments[row] for row in table.SelectedRows]

        if len(selected_segments) != 1: return

        _, position = event.split('::')
        window.perform_long_operation(lambda: player.set_position(getattr(selected_segments[0], position), window), '-TASK-DONE-')

    elif event == '-VIDEO-LOADED-':
        duration_ms = window.metadata['duration_ms']
        filepath = window.metadata['filepath']

        window['-VIDEO-DURATION-'].update(value=seconds_to_position(duration_ms / 1000).split('.')[0])
        window['-FILENAME-'].update(value=filepath.name)

    elif event in('-TIMELINE-', '-VIDEO-NEW-POSITION-'):
        position = window.metadata['position_ms'] / 1000
        window['-VIDEO-POSITION-'].update(value=seconds_to_position(position).split('.')[0])
