from pathlib import Path
from typing import cast
import PySimpleGUI as sg
import yaml

from .controllers.edit_decision_file_dumper import ensure_decision_file_template

from .models.context import SegmentValidatorContext
from .models.events import CONFIGURE_EVENT, PREFILL_NAME_EVENT, SEGMENT_IMPORTED_EVENT, VIDEO_LOADED_EVENT
from .models.keys import OUTPUT_FILENAME_INPUT_KEY, SEGMENT_TIMELINE_KEY

from .views.status_bar import layout as status_bar
from .views.detector_selector import layout as detector_selector, handle_detector
from .views.media_control import layout as media_control, handle_media_control
from .views.timeline import layout as timeline, handle_timeline
from .views.segments_timeline import layout as segments_timeline, handle_segments_timeline
from .views.segments_list import layout as segments_list, render_values, handle_segments_list
from .views.video import layout as video, handle_video

from settings import Settings

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
        [sg.Button('Validate and quit', size=(31, 0), pad=((0, 0), (5, 0)))]
    ]

    return [
        [sg.Column([[
            sg.Text('Review the segments in the right, then click on "Validate and quit"', font='Any 12'),
        ]], element_justification='c', expand_x=True)],
        [
            sg.Push(),
            sg.Column(left_col, expand_x=True, expand_y=True, pad=0),
            sg.VerticalSeparator(),
            sg.Column(right_col, expand_x=True, expand_y=True, pad=0)
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
        event, values = window.read(timeout=500)  # type: ignore
        if event == sg.WIN_CLOSED:
            break

        if event == PREFILL_NAME_EVENT:
            cast(sg.Input, window[OUTPUT_FILENAME_INPUT_KEY]).update(value=values[PREFILL_NAME_EVENT])

        for handler in handlers:
            handler(window, event, values)

    window.close()
