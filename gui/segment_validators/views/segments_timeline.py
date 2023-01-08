from typing import Any, cast
import PySimpleGUI as sg

GRAPH_SIZE = (480, 30)

segments_timeline = [
    sg.Graph(
        canvas_size=GRAPH_SIZE, graph_bottom_left=(0.,0.), graph_top_right=(1.,1.),   # Define the graph area
        float_values=True,
        change_submits=True,    # mouse click events
        background_color='#a6b2be',
        pad=0,
        metadata={'position': None},
        key='-SEGMENTS-TIMELINE-'
    )
]

def handle_segments_timeline(window: sg.Window, event: str, values: dict[str, Any]):
    player = window.metadata['media_player']
    graph = cast(sg.Graph, window['-SEGMENTS-TIMELINE-'])

    if event == '-VIDEO-LOADED-':
        position_handle = graph.draw_line((0.,0.), (0.,1.), color='red')
        graph.metadata['position'] = position_handle
    elif event == '-TIMELINE-' or player.is_playing():
        graph.relocate_figure(graph.metadata['position'], player.get_position(), 0)
