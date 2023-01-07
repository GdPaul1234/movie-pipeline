from pathlib import Path
import unittest

from movie_pipeline.lib.title_cleaner import TitleCleaner

blacklist_path = Path(__file__).parent.parent.joinpath('ressources', 'test_title_re_blacklist.txt')


class TestTitleCleaner(unittest.TestCase):
    def test_clean_title_remove_junk_following_blacklist(self):
        title_cleaner = TitleCleaner(blacklist_path)
        actual_title = title_cleaner.clean_title('Arrête-moi si tu peux (VM)')

        self.assertEqual('Arrête-moi si tu peux', actual_title)

    def test_clean_title_remove_episode_number_following_blacklist(self):
        title_cleaner = TitleCleaner(blacklist_path)
        actual =  title_cleaner.clean_title("Le peuple des forêts (1-3) - L'âge de glace")

        self.assertEqual("Le peuple des forêts - L'âge de glace", actual)
