import json
import logging
from pathlib import Path
from typing import Any, cast
from rich.progress import Progress
from deffcode import Sourcer
import cv2

from lib.ffmpeg_with_progress import ffmpeg_frame_producer
from lib.title_extractor import load_metadata
from lib.ui_factory import transient_task_progress
from models.detected_segments import humanize_segments
from util import seconds_to_position, timed_run

logger = logging.getLogger(__name__)


result_window_name = 'Match Template Result'
segments_min_duration = 20.
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
        if len(self._segments) == 0 or position - self._segments[-1]['end'] > segments_min_duration:
            self._segments.append({'start': position, 'end': position, 'duration': 0})
            logger.debug('Add segment at %f s', position)
            logger.debug('Updated segements: %s', self._segments)
        else:
            self._segments[-1]['end'] = position
            self._segments[-1]['duration'] = position - self._segments[-1]['start']

    def _draw_detection_box(self,
                            image: cv2.Mat,
                            template_shape: tuple[int, int],
                            result: tuple[float, tuple[int, int]],
                            stats):
        w, h = template_shape
        max_val, pt = result

        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        if max_val >= threshold:
         cv2.rectangle(image, pt, (pt[0] + w, pt[1] + h), (0,0,255), 2) # type: ignore

        y0, dy, text = 0, 40, json.dumps(stats, indent=0)
        for i, line in enumerate(text.replace('}', '').split('\n')):
            y = y0 + i*dy
            cv2.putText(image, line, (25, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA, False)

        cv2.imshow(result_window_name, image)
        cv2.resizeWindow(result_window_name, 960, 540)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            return True

        return False

    def detect(self):
        template, t_width, t_height = self._read_template()

        sourcer = Sourcer(str(self._video_path)).probe_stream()
        video_metadata = cast(dict[str, Any], sourcer.retrieve_metadata())

        target_fps = 5
        duration = video_metadata['source_duration_sec']
        cv2.namedWindow(result_window_name, cv2.WINDOW_NORMAL)

        with Progress() as progress:
            try:
                with transient_task_progress(progress, description='match_template', total=duration) as task_id:
                    for frame, _, position_in_s in ffmpeg_frame_producer(self._video_path, target_fps=target_fps):
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
                                "fps": round(target_fps / process_time, 3),
                                "position": seconds_to_position(position_in_s),
                                "segments": humanize_segments(self._segments)
                            }
                            if self._draw_detection_box(image, image_shape, match_result, stats):
                                break
            finally:
                cv2.destroyAllWindows()

        logger.debug('Final segements before cleaning: %s', self._segments)
        return self._segments
