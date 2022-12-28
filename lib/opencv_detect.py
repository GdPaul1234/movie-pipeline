import logging
import os
from pathlib import Path
from rich.progress import Progress
from typing import Any
import cv2

from lib.title_extractor import load_metadata
from lib.ui_factory import transient_task_progress
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

    def _read_video(self) -> tuple[Any, int, int]:
        cap = cv2.VideoCapture(
            str(self._video_path),
            cv2.CAP_FFMPEG,
            (cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
        )

        if cap.isOpened() == False:
            raise ValueError('Error while trying to read video. Please check path again')

        return cap, cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    def _read_template(self) -> tuple[cv2.Mat, int, int]:
        template = cv2.imread(str(self._template_path), cv2.IMREAD_GRAYSCALE)
        width, height = template.shape[::-1]

        return template, width, height

    def _update_segments(self, position: float):
        if len(self._segments) == 0 or self._segments[-1]['end'] - position > segments_min_duration:
            self._segments.append({'start': position, 'end': position, 'duration': 0})
            logger.debug('Add segment at %f s', position)
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

        cv2.putText(image, str(stats), (15, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0),
                    2, lineType=cv2.LINE_AA)

        cv2.imshow(result_window_name, image)
        cv2.resizeWindow(result_window_name, 960, 540)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            return True

        return False

    def detect(self):
        cap, *_ = self._read_video()
        template, t_width, t_height = self._read_template()

        frame_count, fps = cap.get(cv2.CAP_PROP_FRAME_COUNT), cap.get(cv2.CAP_PROP_FPS)
        duration = frame_count / fps

        logger.debug(f'{frame_count=}, {fps=}, {duration=}')
        cv2.namedWindow(result_window_name, cv2.WINDOW_NORMAL)

        with Progress() as progress:
            try:
                with transient_task_progress(progress, description='match_template', total=frame_count) as task_id:
                    # Capture each frame until end of video
                    while cap.isOpened():
                        try:
                            ret, frame = cap.read()

                            current_frame_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
                            if current_frame_pos >= (frame_count - 100):
                                break

                            if ret and current_frame_pos % 5 == 0:
                                image = frame.copy()
                                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                                def match_template(image):
                                   return cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)

                                result, process_time = timed_run(match_template, image)
                                _, max_val, _, max_loc = cv2.minMaxLoc(result)

                                position_in_s = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.
                                progress.update(task_id, completed=current_frame_pos)

                                if max_val >= threshold:
                                    self._update_segments(position_in_s)

                                if logger.isEnabledFor(logging.DEBUG):
                                    image_shape = (t_width, t_height)
                                    match_result = (max_val, max_loc)
                                    stats = { "fps": round(1/process_time, 1), "position": seconds_to_position(position_in_s) }
                                    if self._draw_detection_box(image, image_shape, match_result, stats):
                                        break

                        except KeyboardInterrupt:
                            break
            finally:
                cap.release()
                cv2.destroyAllWindows()

        return self._segments
