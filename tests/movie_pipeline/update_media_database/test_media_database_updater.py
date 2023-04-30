from pathlib import Path
import shutil
import unittest

from ..concerns import copy_files, get_output_movies_directories, create_output_movies_directories, lazy_load_config_file
from movie_pipeline.commands.update_media_database import MediaDatabaseUpdater
from movie_pipeline.lib.nfo_parser import NfoParser

nfo_ressource_dir_path = Path(__file__).parent.parent.parent.joinpath('lib', 'ressources')

output_dir_path, output_dir_movie_path, output_dir_serie_path, backup_dir_path = \
    get_output_movies_directories(Path(__file__).parent)

sample_video_path = Path(__file__).parent.parent.joinpath('ressources', 'counter-30s.mp4')
movie_path = output_dir_movie_path.joinpath('Ant-Man et la Guêpe', 'Ant-Man et la Guêpe.mp4')
movie_path_nfo = movie_path.with_suffix('.nfo')
serie_path = output_dir_serie_path.joinpath('MODERN FAMILY', 'Saison 8', 'MODERN FAMILY S08E22.mp4')
serie_path_nfo = serie_path.with_suffix('.nfo')
tvshow_nfo_path = serie_path_nfo.parent.parent.with_name('tvshow.nfo')

lazy_config = lazy_load_config_file(Path(__file__).parent)


class TestMediaDatabaseUpdater(unittest.TestCase):
    def setUp(self) -> None:
        create_output_movies_directories(Path(__file__).parent)

        copy_files([
            {'source': sample_video_path, 'destination': movie_path},
            {'source': nfo_ressource_dir_path.joinpath('Ant-Man et la Guêpe.nfo'), 'destination': movie_path_nfo},
            {'source': sample_video_path, 'destination': serie_path},
            {'source': nfo_ressource_dir_path.joinpath('MODERN FAMILY S08E22.nfo'), 'destination': serie_path_nfo},
            {'source': nfo_ressource_dir_path.joinpath('tvshow.nfo'), 'destination': tvshow_nfo_path}
        ])

    def test_movie_insert(self):
        config = lazy_config()
        media_database_updater = MediaDatabaseUpdater(config.MediaDatabase.db_path) # type:ignore

        media_database_updater.insert_media(movie_path_nfo, nfo=NfoParser.parse(movie_path_nfo))
        self.assertEqual({movie_path}, media_database_updater.inserted_medias)

        media_database_updater.close()

    # def test_serie_insert(self):
    #     config = lazy_config()
    #     media_database_updater = MediaDatabaseUpdater(config.MediaDatabase.db_path) # type:ignore

    #     media_database_updater.insert_media(movie_path_nfo, nfo=NfoParser.parse(serie_path_nfo))
    #     self.assertTrue('Modern Family' in media_database_updater._inserted_series)
    #     self.assertEqual({serie_path}, media_database_updater.inserted_medias)

    #     media_database_updater.close()

    def tearDown(self) -> None:
        shutil.rmtree(output_dir_path)
