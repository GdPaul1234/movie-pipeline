from pathlib import Path
from typing import cast

import PySimpleGUI as sg
import yaml

from settings import Settings

from .controllers.edit_decision_file_dumper import ensure_decision_file_template
from .models.context import SegmentValidatorContext

from .models.events import (
    CONFIGURE_EVENT,
    PREFILL_NAME_EVENT,
    SEGMENT_IMPORTED_EVENT,
    TOGGLE_MEDIA_SELECTOR_VISIBILITY_EVENT,
    VIDEO_LOADED_EVENT
)

from .models.keys import (
    MEDIA_SELECTOR_CONTAINER_KEY,
    OUTPUT_FILENAME_INPUT_KEY,
    SEGMENT_TIMELINE_KEY,
    TOGGLE_MEDIA_SELECTOR_VISIBILITY_KEY
)

from .views.detector_selector import handle_detector, layout as detector_selector
from .views.media_control import handle_media_control, layout as media_control
from .views.media_selector_list import layout as media_selector_list
from .views.segments_list import handle_segments_list, layout as segments_list, render_values
from .views.segments_timeline import handle_segments_timeline, layout as segments_timeline
from .views.status_bar import layout as status_bar
from .views.timeline import handle_timeline, layout as timeline
from .views.video import handle_video, layout as video

TEXTS = {
    'movies_to_be_processed': 'Movies to be reviewed'.center(40),
    'movie_to_be_validated': 'Movie to be validated'.center(40),
    'review_segments_description': 'Review the segments in the right, then click on "Validate"'
}


def create_window():
    window = sg.Window('Segments Reviewer', main_layout(), finalize=True, resizable=True, use_default_focus=False)
    window.set_min_size(window.size)
    window.bring_to_front()
    window.force_focus()
    return window


def init_metadata(window: sg.Window, filepath: Path, config: Settings):
    window.metadata = SegmentValidatorContext.init_context(filepath, config)

    window.write_event_value(VIDEO_LOADED_EVENT, True)
    window.write_event_value(SEGMENT_IMPORTED_EVENT, True)


def prefill_name(window: sg.Window, filepath: Path, config: Settings):
    if ensure_decision_file_template(filepath, config):
        template_path = filepath.with_suffix(f'{filepath.suffix}.yml.txt')
        template = yaml.safe_load(template_path.read_text(encoding='utf-8'))
        window.write_event_value(PREFILL_NAME_EVENT, template['filename'])
    else:
        sg.popup_auto_close(f'Validated segments already exists for {filepath}', title='Aborting segments validation')
        window.write_event_value(sg.WIN_CLOSED, True)


def main_layout():
    left_col = [
        [sg.VPush()],
        video(),
        timeline(), segments_timeline(),
        [sg.Sizer(0, 10)],
        media_control(),
        [sg.VPush()],
        status_bar()
    ]

    right_col = [
        detector_selector(),
        segments_list(),
        [sg.Input('Nom du fichier converti.mp4', size=(36, 0), pad=((0, 0), (5, 0)), key=OUTPUT_FILENAME_INPUT_KEY)],
        [sg.Button('Validate', size=(31, 0), pad=((0, 0), (5, 0)))]
    ]

    return [
        [
            [sg.VPush()],
            sg.Column([
                [sg.Text(TEXTS['review_segments_description'], font='Any 12'),]
            ], element_justification='c', expand_x=True)
        ],
        [
            sg.Column([
                [
                    sg.pin(
                        sg.Frame(TEXTS['movies_to_be_processed'], [
                            media_selector_list()
                        ], key=MEDIA_SELECTOR_CONTAINER_KEY, visible=False, expand_x=True, expand_y=True, pad=0),
                    )
                ],
                [
                    sg.Button(
                        '>>',
                        key=TOGGLE_MEDIA_SELECTOR_VISIBILITY_KEY,
                        tooltip='Toogle visibility of media selector',
                        size=(3, 1)
                    )
                ]
            ], element_justification='r', expand_x=True, expand_y=True),
            sg.Frame(TEXTS['movie_to_be_validated'], [
                [
                    sg.Push(),
                    sg.Column(left_col, expand_x=True, expand_y=True, pad=0),
                    sg.VerticalSeparator(),
                    sg.Column(right_col, expand_x=True, expand_y=True, pad=0)
                ]
            ], expand_x=True, expand_y=True),
            sg.Push()
        ]
    ]


handlers = (
    handle_detector,
    handle_timeline,
    handle_segments_timeline,
    handle_segments_list,
    handle_media_control,
    handle_video,
)


def main(filepath: Path, config: Settings):
    window = create_window()
    init_metadata(window, filepath, config)
    prefill_name(window, filepath, config)

    window[SEGMENT_TIMELINE_KEY].expand(True, False, False)
    window.bind('<Configure>', CONFIGURE_EVENT)
    render_values(window)

    while True:
        event, values = window.read(timeout=40)  # type: ignore
        if event == sg.WIN_CLOSED:
            break

        if event == PREFILL_NAME_EVENT:
            cast(sg.Input, window[OUTPUT_FILENAME_INPUT_KEY]).update(value=values[PREFILL_NAME_EVENT])

        elif event == TOGGLE_MEDIA_SELECTOR_VISIBILITY_EVENT:
            media_selector_container = cast(sg.Frame, window[MEDIA_SELECTOR_CONTAINER_KEY])
            toggle_media_selector_button = cast(sg.Button, window[TOGGLE_MEDIA_SELECTOR_VISIBILITY_KEY])

            media_selector_container_visibility = not media_selector_container.visible
            toggle_media_selector_button.update(text='<<' if media_selector_container_visibility else '>>')
            media_selector_container.update(visible=media_selector_container_visibility)

        for handler in handlers:
            handler(window, event, values)

    window.close()
