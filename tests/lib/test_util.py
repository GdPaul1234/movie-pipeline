import unittest

from util import progress_to_task_iterator

class TestUtil(unittest.TestCase):
    def test_progress_to_task_iterator(self):
        progress_iterator = (x for x in [0.01, 0.012, 0.015, 0.2, 0.5, 0.7, 1.0])
        expected_task_iterator = range(101)

        actual_task_iterator = progress_to_task_iterator(progress_iterator)

        self.assertEqual(list(expected_task_iterator), list(actual_task_iterator))
