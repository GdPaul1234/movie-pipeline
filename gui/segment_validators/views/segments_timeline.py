import PySimpleGUI as sg

GRAPH_SIZE = (480, 20)

segments_timeline = [
    sg.Graph(
        canvas_size=GRAPH_SIZE, graph_bottom_left=(0, 0), graph_top_right=GRAPH_SIZE,   # Define the graph area
        change_submits=True,    # mouse click events
        key='-SEGMENTS-TIMELINE-'
    )
]
