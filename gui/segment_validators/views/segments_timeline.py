from typing import Any, cast
import PySimpleGUI as sg

GRAPH_SIZE = (480, 30)
right_click_menu = ['&Segments', ['&Add segment', '!&Edit segment',]]

segments_timeline = [
    sg.Graph(
        # Define the graph area
        canvas_size=GRAPH_SIZE, graph_bottom_left=(0., 0.), graph_top_right=(1., 1.),
        float_values=True,
        change_submits=True, # mouse click events
        background_color='#a6b2be',
        right_click_menu=right_click_menu,
        pad=0,
        metadata={'position': None, 'segments': []},
        key='-SEGMENTS-TIMELINE-'
    )
]


def draw_segments(window: sg.Window):
    graph = cast(sg.Graph, window['-SEGMENTS-TIMELINE-'])
    duration_ms = window.metadata['duration_ms']

    for fid in graph.metadata['segments']:
        graph.delete_figure(fid)
    graph.metadata['segments'].clear()

    for segment in window.metadata['segment_container'].segments:
        top_left = (1000*segment.start / duration_ms , 1.)
        bottom_right = (1000*segment.end / duration_ms, 0.)
        rect = graph.draw_rectangle(top_left, bottom_right, fill_color='#283b5b')

        graph.send_figure_to_back(rect)
        graph.metadata['segments'].append(rect)


def handle_segments_timeline(window: sg.Window, event: str, values: dict[str, Any]):
    player = window.metadata['media_player']
    graph = cast(sg.Graph, window['-SEGMENTS-TIMELINE-'])

    if event == '-VIDEO-LOADED-':
        position_handle = graph.draw_line((0.,0.), (0.,1.), color='red')
        graph.metadata['position'] = position_handle

    if event == '-SEGMENTS-UPDATED-':
        draw_segments(window)

    elif event == '-TIMELINE-' or player.is_playing():
        graph.relocate_figure(graph.metadata['position'], player.get_position(), 0)
