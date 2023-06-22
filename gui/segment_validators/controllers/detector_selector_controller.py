from typing import Any, cast

import PySimpleGUI as sg

from movie_pipeline.models.movie_segments import MovieSegments

from ..models.context import SegmentValidatorContext
from ..models.events import SELECTED_DETECTOR_UPDATED_EVENT
from ..models.keys import DETECTOR_SELECTOR_KEY
from ..models.segment_container import Segment, SegmentContainer

from ..controllers.segments_list_controller import delete_segments

from ..views.segments_list import render_values


def populate_detector_selector(window: sg.Window, _event: str, _values: dict[str, Any]):
    selector = cast(sg.Combo, window[DETECTOR_SELECTOR_KEY])
    metadata = cast(SegmentValidatorContext, window.metadata)

    # Update available detectors
    detectors = list(metadata.imported_segments.keys())
    selector.update(values=detectors)

    # Import the first detector result if available
    if len(detectors) >= 1:
        selector.update(value=detectors[0])
        window.write_event_value(SELECTED_DETECTOR_UPDATED_EVENT, detectors[0])


def import_segments_from_selected_detector(window: sg.Window, _event: str, values: dict[str, Any]):
    metadata = cast(SegmentValidatorContext, window.metadata)

    metadata.selected_segments = list(metadata.segment_container.segments)
    delete_segments(window, _event, values)

    metadata.segment_container = SegmentContainer()

    imported_detector_segments = MovieSegments(
        raw_segments=metadata.imported_segments[values[DETECTOR_SELECTOR_KEY]]
    )

    for segment in imported_detector_segments.segments:
        metadata.segment_container.add(Segment(*segment))

    render_values(window)
