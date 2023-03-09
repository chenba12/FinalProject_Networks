import unittest
from app.sql_manager import *


class TestSqlManager(unittest.TestCase):
    db_session = None

    def setUp(self):
        global db_session
        db_session = setup_db()
        first_setup()

    def tearDown(self):
        global db_session
        db_session.rollback()
        db_session.close()

    def test_add_game(self):
        game = add_game('Test Game', 'PC', 'JRPG', 10.99, 80.0, 2022)
        self.assertEqual(game[0]['name'], 'Test Game')
        self.assertEqual(game[0]['platform'], 'PC')
        self.assertEqual(game[0]['category'], 'JRPG')
        self.assertEqual(game[0]['price'], 10.99)
        self.assertEqual(game[0]['score'], 80.0)
        self.assertEqual(game[0]['release_year'], 2022)

    def test_get_game_by_id(self):
        game = add_game('Test Game', 'PC', 'JRPG', 10.99, 80.0, 2022)
        game_id = game[0]['id']
        retrieved_game = get_game_by_id(game_id)
        self.assertEqual(game[0], retrieved_game[0])

    def test_get_game_by_name(self):
        add_game('Test Game', 'PC', 'JRPG', 10.99, 80.0, 2022)
        games = get_game_by_name('Test Game')
        self.assertIsInstance(games, list)
        self.assertEqual(games[0]['name'], 'Test Game')

    def test_delete_game(self):
        game = add_game('Test Game', 'PC', 'JRPG', 10.99, 80.0, 2022)
        game_id = game[0]['id']
        delete_game_by_id(game_id)
        with self.assertRaises(ValueError):
            get_game_by_id(game_id)

    def test_get_game_from_price(self):
        delete_all()
        add_game('Super Mario Bros', 'Switch', 'Platformer', 39.99, 9.4, 1985)
        add_game('Pokemon:Yellow', 'Switch', 'Action', 49.99, 9.0, 1998)
        games = get_game_from_price(40)
        self.assertIsNotNone(games)
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]['name'], 'The Legend of Zelda')

    def test_get_game_by_platform(self):
        delete_all()
        add_game('Super Mario Bros', 'Switch', 'Platformer', 39.99, 9.4, 1985)
        add_game('Pokemon:Yellow', 'PC', 'Action', 49.99, 9.0, 1998)
        games = get_games_by_platform("PC")
        self.assertIsNotNone(games)
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]['platform'], 'PC')

    def test_get_game_by_category(self):
        delete_all()
        add_game('Super Mario Bros', 'Switch', 'Platformer', 39.99, 9.4, 1985)
        add_game('Pokemon:Yellow', 'PC', 'Action', 49.99, 9.0, 1998)
        games = get_games_by_category("Platformer")
        self.assertIsNotNone(games)
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]['category'], 'Platformer')

    def test_get_game_by_score(self):
        delete_all()
        add_game('Super Mario Bros', 'Switch', 'Platformer', 39.99, 9.4, 1985)
        add_game('Pokemon:Yellow', 'PC', 'Action', 49.99, 9.0, 1998)
        games = get_games_by_score(9.2)
        self.assertIsNotNone(games)
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]['score'], 9.4)

    def test_get_game_by_year(self):
        delete_all()
        add_game('Super Mario Bros', 'Switch', 'Platformer', 39.99, 9.4, 1985)
        add_game('Pokemon:Yellow', 'PC', 'Action', 49.99, 9.0, 1998)
        games = get_games_by_date(1985)
        self.assertIsNotNone(games)
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]['release_year'], 1985)

    def test_get_game_by_price_range(self):
        delete_all()
        add_game('Super Mario Bros', 'Switch', 'Platformer', 39.99, 9.4, 1985)
        add_game('Pokemon:Yellow', 'PC', 'Action', 49.99, 9.0, 1998)
        games = get_games_between_price_points(39, 50)
        self.assertIsNotNone(games)
        self.assertEqual(len(games), 2)
        self.assertEqual(games[0]['price'], 39.99)

    def test_game_update(self):
        delete_all()
        add_game('Pokemon:Yellow', 'PC', 'Action', 49.99, 9.0, 1998)
        games = udp_update_game(1, 'Pokemon:Red', 'PC', 'JRPG', 49.99, 100, 1996)
        self.assertIsNotNone(games)
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]['name'], 'Pokemon:Red')

    def test_get_game_by_id_invalid_id(self):
        with self.assertRaises(ValueError):
            get_game_by_id(-1)

    def test_get_game_by_name_invalid_name(self):
        with self.assertRaises(ValueError):
            get_game_by_name('Invalid Game Name')

    def test_get_game_by_name_invalid_platform(self):
        with self.assertRaises(ValueError):
            add_game('Pokemon:Yellow', 'Not a platform', 'Action', 49.99, 9.0, 1998)

    def test_get_game_by_name_invalid_category(self):
        with self.assertRaises(ValueError):
            add_game('Pokemon:Yellow', 'PC', 'Not a category', 49.99, 9.0, 1998)

    def test_get_game_by_name_invalid_year(self):
        with self.assertRaises(ValueError):
            add_game('Pokemon:Yellow', 'PC', 'Action', 49.99, 9.0, 1)

    def test_get_game_by_name_invalid_score(self):
        with self.assertRaises(ValueError):
            add_game('Pokemon:Yellow', 'PC', 'Action', 49.99, 101, 1998)
