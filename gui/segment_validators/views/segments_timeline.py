from typing import Any, cast
import PySimpleGUI as sg

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
            metadata={'position': None, 'segments': []},
            key='-SEGMENTS-TIMELINE-'
        )
    ]


def draw_segments(window: sg.Window):
    graph = cast(sg.Graph, window['-SEGMENTS-TIMELINE-'])
    duration_ms = window.metadata['duration_ms']

    for segment in graph.metadata['segments']:
        graph.delete_figure(segment['fid'])
    graph.metadata['segments'].clear()

    for segment in window.metadata['segment_container'].segments:
        top_left = (1000*segment.start / duration_ms, 1.)
        bottom_right = (1000*segment.end / duration_ms, 0.)
        fill_color = '#f0f3f7' if segment in window.metadata['selected_segments'] else '#283b5b'

        rect = graph.draw_rectangle(top_left, bottom_right, fill_color=fill_color)
        graph.send_figure_to_back(rect)
        graph.metadata['segments'].append({'fid': rect, 'value': segment})


def handle_segments_timeline(window: sg.Window, event: str, values: dict[str, Any]):
    graph = cast(sg.Graph, window['-SEGMENTS-TIMELINE-'])
    position_in_percent = window.metadata['position_ms'] / window.metadata['duration_ms']

    if event == '-VIDEO-LOADED-':
        position_handle = graph.draw_line((0., 0.), (0., 1.), color='red')
        graph.metadata['position'] = position_handle

    elif event == '-CONFIGURE-':
        graph.CanvasSize = graph.get_size()
        graph.relocate_figure(graph.metadata['position'], position_in_percent, 0)
        draw_segments(window)
        window.refresh()

    elif event == '-SEGMENTS-UPDATED-':
        draw_segments(window)

    elif event == '-SEGMENTS-TIMELINE-':
        if len(figures := graph.get_figures_at_location(values['-SEGMENTS-TIMELINE-'])):
            selected_timeline_segment = next(
                (segment['value'] for segment in graph.metadata['segments'] if segment['fid'] == figures[0]),
                None
            )
            window.metadata['selected_segments'] = [selected_timeline_segment]
            window.write_event_value('-SEGMENT-TIMELINE-SELECTED-', selected_timeline_segment)

    elif event in ('-TIMELINE-', '-VIDEO-NEW-POSITION-'):
        graph.relocate_figure(graph.metadata['position'], position_in_percent, 0)
