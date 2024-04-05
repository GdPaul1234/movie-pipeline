import json
import logging

import cv2

from ...lib.util import seconds_to_position
from ...models.detected_segments import DetectedSegment

logger = logging.getLogger(__name__)


def draw_detection_box(result_window_name: str,
                       image: cv2.typing.MatLike,
                       template_shape: cv2.typing.Point,
                       result: tuple[float, cv2.typing.Point],
                       threshold: float,
                       stats):
    w, h = template_shape
    max_val, pt = result

    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    if max_val >= threshold:
        cv2.rectangle(image, pt, (pt[0] + w - 1, pt[1] + h - 1), (0, 0, 255), 2)

    image = resize_with_pad(image, (1920, 1080), color=(0, 0, 0))

    y0, dy, text = 0, 40, json.dumps({'fps': stats['fps'], 'position': seconds_to_position(stats['position'])}, indent=0)
    for i, line in enumerate(text.replace('}', '').split('\n')):
        y = y0 + i*dy
        cv2.putText(image, line, (25, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA, False)

    draw_segments(image, stats['segments'], stats['duration'], stats['position'])

    cv2.imshow(result_window_name, image)
    cv2.resizeWindow(result_window_name, 960, 540)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        return True

    return False


def resize_with_pad(image: cv2.typing.MatLike, new_shape: cv2.typing.Point, color=(255, 255, 255)):
    """Maintains aspect ratio and resizes with padding.

    source: https://gist.github.com/IdeaKing/11cf5e146d23c5bb219ba3508cca89ec

    Params:
        image: Image to be resized.
        new_shape: Expected (width, height) of new image.
        padding_color: Tuple in BGR of padding color
    Returns:
        image: Resized image with padding
    """
    original_shape = (image.shape[1], image.shape[0])

    cv2.resize(image, new_shape)

    delta_w = abs(new_shape[0] - original_shape[0])
    delta_h = abs(new_shape[1] - original_shape[1])
    top, bottom = delta_h//2, delta_h-(delta_h//2)
    left, right = delta_w//2, delta_w-(delta_w//2)

    image = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return image


def draw_segments(image: cv2.typing.MatLike, segments: list[DetectedSegment], duration: float, position: float):
    i_width, i_height = (image.shape[1], image.shape[0])

    x, y = 0, round(0.9 * i_height)

    cv2.rectangle(image, (x, y), (i_width, i_height), (255,255,255), cv2.FILLED)

    for segment in segments:
        cv2.rectangle(
            image,
            (round(x + segment['start'] * i_width / duration), y),
            (round(x + segment['end'] * i_width / duration), i_height),
            (255, 0, 0),
            cv2.FILLED
        )

    position_x = round(x + position * i_width / duration)
    cv2.line(image, (position_x, y), (position_x, i_height), (0, 0, 255), 8)
