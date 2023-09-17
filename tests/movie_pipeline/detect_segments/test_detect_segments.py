from typing import cast
import unittest

from movie_pipeline.models.detected_segments import DetectedSegment, humanize_segments, merge_adjacent_segments


class TestDetectSegments(unittest.TestCase):
    def test_humanize_segments(self):
        segments = [
            {'start': 44.4012, 'end': 368.355, 'duration': 323.954},
            {'start': 612.856, 'end': 1098.44, 'duration': 485.588},
            {'start': 2053.96, 'end': 2519.26, 'duration': 465.3}
        ]
        expected = '00:00:44.401-00:06:08.355,00:10:12.856-00:18:18.440,00:34:13.960-00:41:59.260'

        actual = humanize_segments(cast(list[DetectedSegment], segments))

        self.assertEqual(expected, actual)


    def test_merge_adjacent_segments(self):
        self.maxDiff = None

        segments = [
            {'start': 44.4012, 'end': 368.355, 'duration': 323.954},
            {'start': 612.856, 'end': 1098.44, 'duration': 485.588},
            {'start': 2053.96, 'end': 2519.26, 'duration': 465.3},
            {'start': 2519.26, 'end': 3020.42, 'duration': 501.16},
            {'start': 3020.42, 'end': 3664.78, 'duration': 644.36},
            {'start': 3664.79, 'end': 4271.73, 'duration': 606.938},
            {'start': 4271.73, 'end': 4596.66, 'duration': 324.932},
            {'start': 4883.65, 'end': 6164.9, 'duration': 1281.25},
            {'start': 6678.2, 'end': 6980.4, 'duration': 302.205},
            {'start': 6980.41, 'end': 7686.82, 'duration': 706.414},
            {'start': 7686.82, 'end': 8646.66, 'duration': 959.839},
            {'start': 8646.66, 'end': 9021.17, 'duration': 374.506},
            {'start': 9021.17, 'end': 9362.86, 'duration': 341.694},
            {'start': 9362.86, 'end': 10799.9, 'duration': 1437.04}
        ]
        expected = [
            {'start': 44.4012, 'end': 368.355, 'duration': 323.95},
            {'start': 612.856, 'end': 1098.44, 'duration': 485.59},
            {'start': 2053.96, 'end': 4596.66,'duration': 2542.7},
            {'start': 4883.65, 'end': 6164.9, 'duration': 1281.25},
            {'start': 6678.2,'end': 9362.86,'duration': 2684.67},
            {'start': 9362.86, 'end': 10799.9, 'duration': 1437.04}
        ]

        actual = merge_adjacent_segments(cast(list[DetectedSegment], segments))

        self.assertEqual(expected, actual)
