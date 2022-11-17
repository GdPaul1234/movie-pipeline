import unittest

from movie_file import LegacyMovieFile

class MovieFileTest(unittest.TestCase):
    def test_movie_isserie(self):
        input_path = 'channel 1_Movie Name_2022-11-1601-20.mp4'
        media = LegacyMovieFile(input_path)
        self.assertFalse(media.is_serie)

    def test_serie_isserie(self):
        input_path = 'channel 1_Serie Name S01E23_2022-11-1601-20.mp4'
        media = LegacyMovieFile(input_path)
        self.assertFalse(media.is_serie)
