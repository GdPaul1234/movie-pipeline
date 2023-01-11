import time
from pathlib import Path
from typing import cast
import PySimpleGUI as sg
import yaml
import vlc

from .lib.vlc_instance import create_vlc_player
from movie_pipeline.lib.title_extractor import NaiveTitleExtractor
from movie_pipeline.lib.title_cleaner import TitleCleaner

from .controllers.import_segments_from_file import SegmentImporter
from .controllers.edit_decision_file_dumper import ensure_decision_file_template

from .models.segment_container import SegmentContainer

from .views.status_bar import status_bar
from .views.detector_selector import detector_selector, handle_detector
from .views.media_control import media_control, handle_media_control
from .views.timeline import timeline, handle_timeline
from .views.segments_timeline import segments_timeline, handle_segments_timeline
from .views.segments_list import segments_list, render_values, handle_segments_list
from .views.video import video


def make_window():
    window = sg.Window('Segments Reviewer', layout, finalize=True, resizable=True, use_default_focus=False)
    window.set_min_size(window.size)
    window.bring_to_front()
    window.force_focus()

    window.metadata = {
        'segment_container': SegmentContainer(),
        'media_player': create_vlc_player(window),
        'selected_segments': [],
        'filepath': Path(''),
        'imported_segments': {},
        'duration_ms': 0,
        'config': None
    }

    return window


def load_media(window: sg.Window, filepath: Path):
    media_player = window.metadata['media_player']

    media = vlc.Media(filepath)
    media_player.set_media(media)

    media_player.play()
    time.sleep(0.5)
    duration_ms = media_player.get_length()
    media_player.pause()

    window.metadata['duration_ms'] = duration_ms
    window.metadata['filepath'] = filepath
    window.write_event_value('-VIDEO-LOADED-', True)


def import_segment(window: sg.Window, filepath: Path):
    window.metadata['imported_segments'] = SegmentImporter(filepath).import_segments()
    window.write_event_value('-SEGMENTS-IMPORTED-', True)


def prefill_name(window: sg.Window, filepath: Path, config):
    if ensure_decision_file_template(filepath, config):
        template_path = filepath.with_suffix(f'{filepath.suffix}.yml.txt')
        template = yaml.safe_load(template_path.read_text(encoding='utf-8'))
        window.write_event_value('-PREFILL-NAME-', template['filename'])
    else:
        sg.popup_auto_close(f'Validated segments already exists for {filepath}', title='Aborting segments validation')
        window.write_event_value(sg.WIN_CLOSED, True)


left_col = [
    [sg.VPush()],
    video,
    timeline, segments_timeline,
    [sg.Sizer(0, 10)],
    media_control,
    [sg.VPush()],
    status_bar
]

right_col = [
    detector_selector,
    segments_list,
    [sg.Input('Nom du fichier converti.mp4', size=(35, 0), pad=((0,0), (5,0)), key='-NAME-')],
    [sg.Button('Validate and quit', size=(30, 0), pad=((0,0), (5,0)))]
]

layout = [
    [sg.Column([[
        sg.Text('Review the segments in the right, then click on "Validate and quit"', font='Any 12'),
    ]], element_justification='c', expand_x=True)],
    [
        sg.Push(),
        sg.Column(left_col, expand_x=True, expand_y=True, pad=0),
        sg.VerticalSeparator(),
        sg.Column(right_col, expand_x=True, expand_y=True, pad=0),
    ]
]

handlers = (
    handle_media_control,
    handle_timeline,
    handle_segments_timeline,
    handle_segments_list,
    handle_detector
)


def main(filepath: Path, config):
    window = make_window()
    window.metadata['config'] = config

    load_media(window, filepath)
    import_segment(window, filepath)
    prefill_name(window, filepath, config)

    window['-VID-OUT-'].expand(True, True)
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
