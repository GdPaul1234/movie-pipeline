import unittest

from pathlib import Path
from movie_pipeline.lib.nfo_parser import NfoParser, TvShowNfo, SerieNfo, MovieNfo
from datetime import date

ressource_dir_path = Path(__file__).parent.joinpath('ressources')

class TestNfoParser(unittest.TestCase):
    def test_tv_show_nfo_parsing(self):
        nfo_path = ressource_dir_path.joinpath('tvshow.nfo')
        parsed_data = NfoParser.parse(nfo_path)

        expected_parsed_data = TvShowNfo(
            title='Modern Family',
            ratings=[7.7],
            rating=7.7,
            plot='Quand les familles Pritchett, Delgado et Dunphy acceptent qu\'un documentaire soit tourné sur leurs '
                 'vies, elles étaient loin d\'imaginer qu\'elles allaient tant en révéler... Jay Pritchett a rencontré '
                 'la très sexy Colombienne Gloria Delgado le jour où sa femme l\'a quitté. Leur différence d\'âge est '
                 'pour lui un challenge de tous les jours. Sa fille, Claire, a elle-même bien du mal à gérer sa vie de '
                 'famille depuis que son mari, Phil, est persuadé d\'être en phase avec ses enfants adolescents alors '
                 'qu\'il ne fait que les embarrasser ! Quant au frère de Claire, Mitchell, il vit avec son petit-ami '
                 'Cameron et ils viennent d\'adopter Lily, une petite Vietnamienne...',
            mpaa='TV-PG',
            genres=['Comédie'],
            premiered=date.fromisoformat('2009-09-23'),
            year=2009,
            actors=['Ed O\'Neill', 'Sofía Vergara', 'Julie Bowen', 'Ty Burrell', 'Jesse Tyler Ferguson']
        )

        self.assertIsInstance(parsed_data, TvShowNfo)
        self.assertEqual(expected_parsed_data, parsed_data)

    def test_serie_nfo_parsing(self):
        nfo_path = ressource_dir_path.joinpath('MODERN FAMILY S08E22.nfo')
        parsed_data = NfoParser.parse(nfo_path)

        expect_parsed_data = SerieNfo(
            title='Les Lauréats',
            showtitle='Modern Family',
            ratings=[7.786],
            rating=7.786,
            season=8,
            episode=22,
            plot='La famille entière se prépare à la remise de diplômes de Luke et de Manny. Javier revient à cette '
                 'occasion et emmène son fils dans un club de strip-tease. Phil et Claire gèrent difficilement l\''
                 'admission de Luke et de leur côté, Mitchell et Cameron se demandent si Lilly est surdouée.',
            mpaa='TV-PG',
            genres=['Comédie'],
            credits=['Jeffrey Richman', 'Jon Pollack'],
            directors=['Steven Levitan'],
            premiered=date.fromisoformat('2009-09-23'),
            year=2017,
            aired=date.fromisoformat('2017-05-17'),
            actors=['Ed O\'Neill', 'Sofía Vergara', 'Julie Bowen', 'Ty Burrell', 'Jesse Tyler Ferguson'],
        )

        self.assertIsInstance(parsed_data, SerieNfo)
        self.assertEqual(expect_parsed_data, parsed_data)

    def test_movie_nfo_parsing(self):
        nfo_path = ressource_dir_path.joinpath('Ant-Man et la Guêpe.nfo')
        parsed_data = NfoParser.parse(nfo_path)

        expect_parsed_data = MovieNfo(
            title='Ant-Man et la Guêpe',
            sorttitle='Ant-Man et la Guêpe',
            ratings=[6.962],
            rating=6.962,
            plot='Après les événements survenus dans Captain America : Civil War, Scott Lang a bien du mal à concilier '
                 'sa vie de super-héros et ses responsabilités de père. Mais ses réflexions sur les conséquences de ses '
                 'choix tournent court lorsque Hope van Dyne et le Dr Hank Pym lui confient une nouvelle mission urgente'
                 '... Scott va devoir renfiler son costume et apprendre à se battre aux côtés de La Guêpe afin de faire '
                 'la lumière sur des secrets enfouis de longue date...',
            tagline='Ant-Man est de retour',
            mpaa='PG-13',
            genres=['Action', 'Aventure', 'Science-Fiction'],
            credits=['Paul Rudd', 'Stan Lee', 'Jack Kirby', 'Larry Lieber', 'Andrew Barrer'],
            directors=['Peyton Reed', 'Karen M. Cantley', 'Robin Meyers', 'Hajar Mainl', 'Hannah Myvanwy Driscoll'],
            premiered=date.fromisoformat('2018-07-04'),
            year=2018,
            actors=['Paul Rudd', 'Evangeline Lilly', 'Michael Peña', 'Walton Goggins', 'Bobby Cannavale']
        )

        self.assertIsInstance(parsed_data, MovieNfo)
        self.assertEqual(expect_parsed_data, parsed_data)

