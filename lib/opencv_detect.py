from configparser import ConfigParser
import json
import logging
from pathlib import Path
from typing import Any, cast
from rich.progress import Progress
from deffcode import Sourcer
import cv2

from lib.ffmpeg_with_progress import ffmpeg_frame_producer
from lib.opencv_annotator import draw_detection_box
from lib.title_extractor import load_metadata
from lib.ui_factory import transient_task_progress
from models.detected_segments import humanize_segments
from util import seconds_to_position, timed_run

logger = logging.getLogger(__name__)

segments_min_gap = 20.
threshold = 0.8


def OpenCVTemplateDetectWithInjectedTemplate(movie_path: Path, config):
    templates_path = Path(config.get('SegmentDetection', 'templates_path'))

    metadata = load_metadata(movie_path)

    if metadata is None:
        raise ValueError('No metadata found. Please retry when the movie is finished')

    template_path = templates_path.joinpath(f"{metadata['channel']}.bmp")

    if not templates_path.exists():
        raise FileNotFoundError(template_path)

    return lambda m: OpenCVTemplateDetect(m, template_path)


class OpenCVTemplateDetect:
    def __init__(self, video_path: Path, template_path: Path) -> None:
        self._video_path = video_path
        self._template_path = template_path

        self._segments = []

    def _read_template(self) -> tuple[cv2.Mat, int, int]:
        template = cv2.imread(str(self._template_path), cv2.IMREAD_GRAYSCALE)
        width, height = template.shape[::-1]

        return template, width, height

    def _update_segments(self, position: float):
        position = round(position, 2)

        if len(self._segments) == 0 or (position - self._segments[-1]['end']) > segments_min_gap:
            self._segments.append({'start': position, 'end': position, 'duration': 0})

            logger.debug('Add segment at %f s', position)
            logger.debug('Updated segments:\n%s', '\n'.join(map(str, self._segments)))
        else:
            self._segments[-1]['end'] = position
            self._segments[-1]['duration'] = round(position - self._segments[-1]['start'], 2)

    def _build_crop_filter(self):
        template_metadata_path = self._template_path.with_suffix('.ini')

        if not template_metadata_path.exists():
            return ''

        config = ConfigParser()
        config.read(template_metadata_path)

        template_metadata = config['General']

        w = template_metadata.getint('x2') - template_metadata.getint('x1')
        h = template_metadata.getint('y2') - template_metadata.getint('y1')
        x, y = template_metadata.getint('x1'), template_metadata.getint('y1')

        return f'crop={w=}:{h=}:{x=}:{y=}'

    def detect(self):
        template, t_width, t_height = self._read_template()

        sourcer = Sourcer(str(self._video_path)).probe_stream()
        video_metadata = cast(dict[str, Any], sourcer.retrieve_metadata())

        target_fps = 5
        duration = video_metadata['source_duration_sec']
        result_window_name = f'Match Template Result - {self._video_path}'

        cv2.namedWindow(result_window_name, cv2.WINDOW_NORMAL)

        with Progress() as progress:
            try:
                with transient_task_progress(progress, description='match_template', total=duration) as task_id:
                    for frame, _, position_in_s in ffmpeg_frame_producer(
                        self._video_path, target_fps=target_fps,
                        other_video_filter=self._build_crop_filter()
                    ):
                        image = frame.copy()

                        def match_template(image):
                            return cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)

                        result, process_time = timed_run(match_template, image)
                        _, max_val, _, max_loc = cv2.minMaxLoc(result)

                        progress.update(task_id, completed=position_in_s)

                        if max_val >= threshold:
                            self._update_segments(position_in_s)

                        if logger.isEnabledFor(logging.DEBUG):
                            image_shape = (t_width, t_height)
                            match_result = (max_val, max_loc)
                            stats = {
                                "fps": round(process_time and target_fps / process_time),
                                "position": seconds_to_position(position_in_s),
                                "segments": humanize_segments(self._segments)
                            }

                            if draw_detection_box(result_window_name, image, image_shape, match_result, threshold, stats):
                                break
            finally:
                cv2.destroyAllWindows()

        logger.debug('Final segments before cleaning: %s', self._segments)
        return self._segments
