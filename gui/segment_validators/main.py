from pathlib import Path
from typing import cast

import PySimpleGUI as sg
from settings import Settings


from .models.events import (
    APPLICATION_LOADED_EVENT,
    CONFIGURE_EVENT,
    PREFILL_NAME_EVENT,
)

from .models.keys import (
    FLASH_TOP_NOTICE_KEY,
    MEDIA_SELECTOR_CONTAINER_KEY,
    MEDIA_SELECTOR_KEY,
    OUTPUT_FILENAME_INPUT_KEY,
    SEGMENT_TIMELINE_KEY,
    SKIP_BACKUP_CHECKBOX_KEY,
    TOGGLE_MEDIA_SELECTOR_VISIBILITY_KEY
)

from .controllers.media_selector_list_controller import load_new_media

from .views.detector_selector import handle_detector, layout as detector_selector
from .views.media_control import handle_media_control, layout as media_control
from .views.media_selector_list import handle_media_selector_list, layout as media_selector_list
from .views.segments_list import handle_segments_list, layout as segments_list, render_values
from .views.segments_timeline import handle_segments_timeline, layout as segments_timeline
from .views.timeline import handle_timeline, layout as timeline
from .views.video import handle_video, layout as video

from .views.texts import TEXTS


def create_window():
    window = sg.Window('Segments Reviewer', main_layout(), finalize=True, resizable=True, use_default_focus=False)
    window.set_min_size(window.size)
    window.bring_to_front()
    window.force_focus()
    return window


def main_layout():
    left_col = [
        [sg.VPush()],
        video(),
        timeline(), segments_timeline(),
        [sg.Sizer(0, 10)],
        media_control(),
        [sg.VPush()]
    ]

    right_col = [
        detector_selector(),
        segments_list(),
        [
            sg.Input('Nom du fichier converti.mp4', size=(25, 0), pad=((0, 0), (5, 0)), key=OUTPUT_FILENAME_INPUT_KEY),
            sg.Checkbox('Skip backup', key=SKIP_BACKUP_CHECKBOX_KEY)
        ],
        [sg.Button('Validate', expand_x=True, pad=((0, 0), (5, 0)))]
    ]

    return [
        [
            [sg.VPush()],
            sg.Column([
                [sg.Text(TEXTS['review_segments_description'], key=FLASH_TOP_NOTICE_KEY, font='Any 12'),]
            ], element_justification='c', expand_x=True)
        ],
        [
            sg.Column([
                [
                    sg.pin(
                        sg.Frame(TEXTS['movies_to_be_processed'], [
                            media_selector_list()
                        ], key=MEDIA_SELECTOR_CONTAINER_KEY, visible=False, size=(250, 1), expand_y=True, pad=0),
                        expand_y=True
                    )
                ],
                [
                    sg.Button(
                        '>>',
                        key=TOGGLE_MEDIA_SELECTOR_VISIBILITY_KEY,
                        tooltip='Toggle visibility of media selector',
                        size=(3, 1)
                    )
                ]
            ], element_justification='r', expand_x=True, expand_y=True),
            sg.Frame(TEXTS['movie_to_be_validated'], [
                [
                    sg.Push(),
                    sg.Column(left_col, expand_x=True, expand_y=True, pad=0),
                    sg.VerticalSeparator(pad=((10, 5), (5, 10))),
                    sg.Column([[sg.Col(right_col, expand_y=True)]], expand_x=True, expand_y=True, pad=0)
                ]
            ], expand_x=True, expand_y=True),
            sg.Push()
        ]
    ]


handlers = (
    handle_media_selector_list,
    handle_detector,
    handle_timeline,
    handle_segments_timeline,
    handle_segments_list,
    handle_media_control,
    handle_video,
)


def main(filepath: Path | list[Path], config: Settings):
    media_paths = [filepath] if isinstance(filepath, Path) else filepath
    first_media_path = filepath if isinstance(filepath, Path) else filepath[0]

    window = create_window()
    window.write_event_value(APPLICATION_LOADED_EVENT, [media_paths])
    load_new_media(window, '', { MEDIA_SELECTOR_KEY: [first_media_path], 'config': config })

    window[SEGMENT_TIMELINE_KEY].expand(True, False, False)
    window.bind('<Configure>', CONFIGURE_EVENT)
    render_values(window)

    while True:
        event, values = window.read(timeout=40) # type: ignore
        if event == sg.WIN_CLOSED:
            break

        if event == sg.TIMEOUT_EVENT:
            continue

        if event == PREFILL_NAME_EVENT:
            cast(sg.Input, window[OUTPUT_FILENAME_INPUT_KEY]).update(value=values[PREFILL_NAME_EVENT])

        for handler in handlers:
            handler(window, event, values)

    window.close()
