from pathlib import Path
from typing import cast
import PySimpleGUI as sg
from deffcode import Sourcer
import yaml

from .lib.simple_video_only_player import SimpleVideoOnlyPlayerConsumer

from .controllers.import_segments_from_file import SegmentImporter
from .controllers.edit_decision_file_dumper import ensure_decision_file_template

from .models.segment_container import SegmentContainer

from .views.status_bar import layout as status_bar
from .views.detector_selector import layout as detector_selector, handle_detector
from .views.media_control import layout as media_control, handle_media_control
from .views.timeline import layout as timeline, handle_timeline
from .views.segments_timeline import layout as segments_timeline, handle_segments_timeline
from .views.segments_list import layout as segments_list, render_values, handle_segments_list
from .views.video import layout as video, handle_video

from settings import Settings

def make_window():
    window = sg.Window('Segments Reviewer', main_layout(), finalize=True, resizable=True, use_default_focus=False)
    window.set_min_size(window.size)
    window.bring_to_front()
    window.force_focus()

    window.metadata = {
        'segment_container': SegmentContainer(),
        'media_player': None,
        'selected_segments': [],
        'filepath': Path(''),
        'imported_segments': {},
        'position_ms': 0,
        'duration_ms': 0,
        'config': None
    }

    return window


def load_media(window: sg.Window, filepath: Path):
    sourcer = Sourcer(str(filepath)).probe_stream()
    metadata = cast(dict, sourcer.retrieve_metadata())

    window.metadata['media_player'] = SimpleVideoOnlyPlayerConsumer(filepath)
    window.metadata['duration_ms'] = 1000 * metadata['source_duration_sec']
    window.metadata['filepath'] = filepath
    window.write_event_value('-VIDEO-LOADED-', True)


def import_segment(window: sg.Window, filepath: Path):
    window.metadata['imported_segments'] = SegmentImporter(filepath).import_segments()
    window.write_event_value('-SEGMENTS-IMPORTED-', True)


def prefill_name(window: sg.Window, filepath: Path, config: Settings):
    if ensure_decision_file_template(filepath, config):
        template_path = filepath.with_suffix(f'{filepath.suffix}.yml.txt')
        template = yaml.safe_load(template_path.read_text(encoding='utf-8'))
        window.write_event_value('-PREFILL-NAME-', template['filename'])
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
        [sg.Input('Nom du fichier converti.mp4', size=(36, 0), pad=((0, 0), (5, 0)), key='-NAME-')],
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
    window = make_window()
    window.metadata['config'] = config

    load_media(window, filepath)
    import_segment(window, filepath)
    prefill_name(window, filepath, config)

    window['-SEGMENTS-TIMELINE-'].expand(True, False, False)
    window.bind('<Configure>', '-CONFIGURE-')
    render_values(window)

    while True:
        event, values = window.read(timeout=500)  # type: ignore
        if event == sg.WIN_CLOSED:
            break

        if event == '-PREFILL-NAME-':
            cast(sg.Input, window['-NAME-']).update(value=values['-PREFILL-NAME-'])

        for handler in handlers:
            handler(window, event, values)

    window.close()
