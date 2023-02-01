from typing import Any, cast
import PySimpleGUI as sg

from movie_pipeline.models.movie_segments import MovieSegments

from ..models.segment_container import SegmentContainer, Segment
from ..views.segments_list import render_values


def layout():
    return [
        sg.Combo(
            [],
            enable_events=True,
            size=(34, 0),
            pad=((0, 0), (5, 5)),
            key='-DETECTOR-'
        )
    ]


def handle_detector(window: sg.Window, event: str, values: dict[str, Any]):
    selector = cast(sg.Combo, window['-DETECTOR-'])
    imported_segments = window.metadata['imported_segments']

    if event == '-SEGMENTS-IMPORTED-':
        detectors = list(imported_segments.keys())
        selector.update(values=detectors)

        if len(detectors) == 1:
            selector.update(value=detectors[0])
            window.write_event_value('-DETECTOR-', detectors[0])

    elif event == '-DETECTOR-':
        imported_segments_container = SegmentContainer()
        imported_detector_segments = MovieSegments(raw_segments=imported_segments[values['-DETECTOR-']])

        for segment in imported_detector_segments.segments:
            imported_segments_container.add(Segment(*segment))

        window.metadata['segment_container'] = imported_segments_container
        render_values(window)
