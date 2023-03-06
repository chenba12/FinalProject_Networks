from message import json_to_message, error_message, result_message
from games import Game, Base, validate_platform, validate_year, validate_category, validate_score, json_to_game
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
import socket
import json

# TCP SERVER

# constants
APP_SERVER_IP = "10.0.2.15"
APP_SERVER_PORT = 30962
APP_CLIENT_PORT = 20961
BUFFER_SIZE = 1024


def start_server() -> None:
    server_socket = socket.socket()  # get instance
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((APP_SERVER_IP, APP_SERVER_PORT))  # bind host address and port together

    server_socket.listen(10)
    connection, address = server_socket.accept()  # accept new connection

    print("Connection from: " + str(address))
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = connection.recv(BUFFER_SIZE)
        if not data:
            break
        request_object = json.loads(data.decode("utf-8"))
        message_object = json_to_message(request_object)
        handle_request(connection, message_object)
    connection.close()  # close the connection


def handle_request(connection, message_object) -> None:
    match str(message_object.func):
        case "getAll":
            print("----------SQL Get All----------")
            try:
                result = get_all()
                send_to_client(connection, result)
            except ValueError:
                error_to_send = error_message("Game Catalog is empty")
                connection.send(bytes(json.dumps(error_to_send), encoding="utf-8"))
        case "addGame":
            print("----------SQL Add Game----------")
            name = message_object.body['name']
            platform = message_object.body['platform']
            category = message_object.body['category']
            price = message_object.body['price']
            release_year = (message_object.body['release_year'])
            score = message_object.body['score']
            try:
                result = add_game(name=name, category=category, platform=platform, price=price,
                                  score=score, release_year=release_year)
                send_to_client(connection, result)
            except ValueError:
                send_error_to_client(connection, "Invalid game parameters")
        case "getGameByID":
            print("----------SQL Get Game By ID----------")
            game_id = message_object.body['id']
            try:
                result = get_game_by_id(game_id)
                send_to_client(connection, result)
            except ValueError:
                send_error_to_client(connection, "Invalid game ID")
        case "getGameByName":
            print("----------SQL Get Game By Name----------")
            game_name = message_object.body['name']
            try:
                result = get_game_by_name(game_name)
                send_to_client(connection, result)
            except ValueError:
                send_error_to_client(connection, "Invalid game name")
        case "getGameByPlatform":
            print("----------SQL Get Games By Platform----------")
            game_platform = message_object.body['platform']
            try:
                result = get_games_by_platform(game_platform)
                send_to_client(connection, result)
            except ValueError:
                send_error_to_client(connection, "Invalid game platform")
        case "getGameByCategory":
            print("----------SQL Get Games By Category----------")
            game_category = message_object.body['category']
            try:
                result = get_games_by_category(game_category)
                send_to_client(connection, result)
            except ValueError:
                send_error_to_client(connection, "Invalid game category")
        case "deleteGame":
            print("----------SQL Delete Game----------")
            game_id = message_object.body['id']
            try:
                result = delete_game_by_id(game_id)
                send_to_client(connection, result)
            except ValueError:
                send_error_to_client(connection, "Invalid game ID")
        case "getGameByScore":
            print("----------SQL Get Games By Score----------")
            score = message_object.body['score']
            try:
                result = get_games_by_score(score)
                send_to_client(connection, result)
            except ValueError:
                send_error_to_client(connection, "Invalid game score")
        case "getGameByYear":
            print("----------SQL Get Games By Year----------")
            release_year = message_object.body['release_year']
            try:
                result = get_games_by_date(release_year)
                send_to_client(connection, result)
            except ValueError:
                send_error_to_client(connection, "Invalid game release year")
        case "getGameByPrice":
            print("----------SQL Get Games By Price----------")
            price = message_object.body['price']
            try:
                result = get_game_from_price(price)
                send_to_client(connection, result)
            except ValueError:
                send_error_to_client(connection, "Invalid price range")
        case "getGameByPriceBetween":
            print("----------SQL Get Games By Price range----------")
            start = message_object.body['start']
            end = message_object.body['end']
            try:
                result = get_games_between_price_points(start, end)
                send_to_client(connection, result)
            except ValueError:
                send_error_to_client(connection, "Invalid price range")
        case "updateGame":
            print("----------SQL Update Game----------")
            game_id = message_object.body['id']
            name = message_object.body['name']
            platform = message_object.body['platform']
            category = message_object.body['category']
            price = message_object.body['price']
            release_year = (message_object.body['release_year'])
            score = message_object.body['score']
            update_game(category, connection, game_id, name, platform, price, release_year, score)

        case _:
            print("Got Invalid error")


def send_error_to_client(connection, message) -> None:
    error_to_send = error_message(message)
    connection.send(bytes(json.dumps(error_to_send.to_json()), encoding="utf-8"))


def send_to_client(connection, result) -> None:
    message_to_send = result_message(result)
    connection.send(bytes(json.dumps(message_to_send.to_json()), encoding="utf-8"))


# Create the app.db and init the db_session
def setup_db() -> None:
    global db_session
    engine = create_engine('sqlite:///app.db', echo=False)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    db_session = session()


# All the methods below that return data from the database return it as a list even if there is only 1 row
def get_all() -> [Game]:
    result = db_session.query(Game).all()
    if result is not None:
        send = []
        for game in result:
            send.append(game.to_json())
        if not send:
            raise ValueError("The Table is Empty")
        else:
            return send


def add_game(name, platform, category, price, score, release_year) -> [Game]:
    print(release_year, platform, category, score)
    if (validate_year(release_year) and validate_platform(platform) and validate_category(
            category) and validate_score(score)):
        game = Game()
        game.name = name
        game.platform = platform
        game.category = category
        game.price = price
        game.score = score
        game.release_year = release_year
        print(game)
        db_session.add(game)
        db_session.commit()
        print(game)
        return get_game_by_id(game.id)
    else:
        raise ValueError("Value Error")


def delete_game_by_id(game_id) -> str:
    result = db_session.query(Game).filter(Game.id == game_id).first()
    if result is None:
        raise ValueError(f"Can't delete game with id {game_id} nothing found")
    else:
        print(f'Deleting....')
        db_session.delete(result)
        return get_all()


def get_game_by_id(game_id) -> [Game]:
    result = db_session.query(Game).filter(Game.id == game_id).first()
    if result is None:
        raise ValueError(f"No game with id {game_id} found")
    else:
        return [result.to_json()]


def get_game_by_name(name) -> [Game]:
    result = db_session.query(Game).filter(Game.name.like(f'{name}%')).all()
    if result is not None:
        send = []
        for game in result:
            send.append(game.to_json())
        if not send:
            raise ValueError("No game found with that name")
        else:
            return send


def get_game_from_price(price) -> [Game]:
    result = db_session.query(Game).filter(Game.price >= price).all()
    if result is not None:
        send = []
        for game in result:
            send.append(game.to_json())
        if not send:
            raise ValueError(f"No games with price greater or equal to {price}")
        else:
            return send


def get_games_by_category(category) -> [Game]:
    result = db_session.query(Game).filter(Game.category == category).all()
    if result is not None:
        send = []
        for game in result:
            send.append(game.to_json())
        if not send:
            raise ValueError(f"No games from category: {category}")
        else:
            return send


def get_games_by_platform(platform):
    if validate_platform(platform):
        result = db_session.query(Game).filter(Game.platform == platform).all()
        if result is not None:
            send = []
            for game in result:
                send.append(game.to_json())
            if not send:
                raise ValueError(f"No games from platform: {platform}")
            else:
                return send
    raise ValueError("not a valid platform")


def get_games_between_price_points(start, end) -> [Game]:
    if start > end:
        raise ValueError("start price can't be larger than end price")
    result = db_session.query(Game).filter(and_(Game.price >= start, Game.price <= end)).all()
    if result is not None:
        send = []
        for game in result:
            send.append(game.to_json())
        if not send:
            raise ValueError(f"No games with price range from {start} to {end}")
        else:
            return send


def get_games_by_date(release_year) -> [Game]:
    validate_year(release_year)
    result = db_session.query(Game).filter(Game.release_year == release_year).all()
    if result is not None:
        send = []
        for game in result:
            send.append(game.to_json())
        if not send:
            raise ValueError(f"No games from year: {release_year}")
        else:
            return send


def get_games_by_score(score) -> [Game]:
    validate_score(score)
    result = db_session.query(Game).filter(Game.score >= score).all()
    if result is not None:
        send = []
        for game in result:
            send.append(game.to_json())
        if not send:
            raise ValueError(f"No games with score: {score}")
        else:
            return send


def update_game(category, connection, game_id, name, platform, price, release_year, score):
    result = db_session.query(Game).filter(Game.id == game_id).first()
    if result is not None or result is not []:
        result.name = name
        result.platform = platform
        result.category = category
        result.price = price
        result.release_year = release_year
        result.score = score
        db_session.commit()
        send_to_client(connection, [result.to_json()])


def delete_all() -> None:
    db_session.query(Game).delete()
    print("Data deleted")


# Initialize the Database
# Delete everything from the previous times the database was used
# Add 30 new rows to the database
def first_setup() -> None:
    delete_all()
    print("First init")
    add_game("God of War", "Playstation4", "Action", 49.99, 94, 2018)
    add_game("Elden Ring", "PC", "Action", 59.99, 96, 2022)
    add_game("Persona 5 Royal", "Playstation4", "JRPG", 23.99, 95, 2019)
    add_game("The Last of Us Part 1", "Playstation5", "Survival", 45.50, 88, 2022)
    add_game("Chained Echoes", "Switch", "JRPG", 40, 91, 2022)
    add_game("Xenoblade Chronicles 3", "Switch", "JRPG", 59.99, 89, 2022)
    add_game("Horizon Forbidden west", "Playstation5", "RPG", 59.99, 88, 2022)
    add_game("Crisis Core: Final Fantasy VII Reunion", "PC", "JRPG", 49.99, 83, 2022)
    add_game("Pokemon Legends: Arceus", "Switch", "JRPG", 59.99, 83, 2022)
    add_game("Marvel's Midnight Suns", "PC", "Action", 49.99, 83, 2022)

    add_game("Hades", "PC", "Action", 49.99, 93, 2021)
    add_game("Final Fantasy XIV: Endwalker", "PC", "MMO", 39.99, 92, 2021)
    add_game("Final Fantasy VII Remake Intergrade", "Playstation5", "JRPG", 39.99, 89, 2021)
    add_game("It Takes Two", "Playstation4", "Adventure", 29.99, 89, 2021)
    add_game("Ratchet & Clank: Rift Apart", "Playstation5", "Adventure", 29.99, 88, 2021)
    add_game("Metroid Dread", "Switch", "Action", 59.99, 87, 2021)
    add_game("Ghost of Tsushima: Director's Cut", "Playstation5", "Action", 29.99, 87, 2021)
    add_game("Persona 5 Strikers", "PC", "Action", 29.99, 81, 2021)
    add_game("Pokemon Brilliant Diamond", "Switch", "JRPG", 59.99, 73, 2021)
    add_game("Destroy All Humans!", "Playstation4", "Action", 20, 66, 2021)

    add_game("The Last of Us Part 2", "Playstation4", "Action", 29.99, 93, 2020)
    add_game("Ori and the Will of the Wisps", "PC", "Platformer", 19.99, 88, 2020)
    add_game("Nioh 2", "Playstation4", "Action", 25.50, 85, 2020)
    add_game("Trials of Mana", "Switch", "JRPG", 19.99, 74, 2020)
    add_game("Dragon Ball Z: Kakarot", "PC", "Adventure", 20, 73, 2020)
    add_game("Destropolis", "Switch", "Shooter", 19.80, 67, 2020)
    add_game("Exit the Gungeon", "PC", "Shooter", 49.99, 67, 2020)
    add_game("Fairy Tail", "PC", "Action", 39.99, 66, 2020)
    add_game("Waking", "PC", "Action", 10, 42, 2020)
    add_game("Jump Force", "Playstation4", "Fighting", 12, 50, 2020)
    print("All entries added...")


# Main to test some methods
if __name__ == '__main__':
    print("--- setup_db() ---")
    setup_db()
    print("--- first_setup() ---")
    first_setup()
    print("--- start_server() ---")
    start_server()
    # print("--- add_game() ---")
    # add_game()
    # print("--- get_all() ---")
    # games_List = get_all()
    # print(games_List)
    # print("--- get_game_by_id() ---")
    # games_List = get_game_by_id(2)
    # print(games_List)
    # print("--- get_game_by_name() ---")
    # games_List = get_game_by_name("Final Fantasy")
    # print(games_List)
    # print("--- delete_game_by_id() ---")
    # delete_game_by_id(2)
    # print("--- get_all() ---")
    # games_List = get_all()
    # print(games_List)
    # print("--- get_game_from_price() ---")
    # games_List = get_game_from_price(40)
    # print(games_List)
    # print("--- get_games_by_platform() ---")
    # games_List = get_games_by_platform("PC")
    # print(games_List)
    # print("--- get_games_from_date() ---")
    # games_List = get_games_from_date(2021)
    # print(games_List)
    # print("--- get_games_between_price_points() ---")
    # games_List = get_games_between_price_points(20, 40)
    # print(games_List)
    # print("--- get_games_by_score() ---")
    # games_List = get_games_by_score(93)
    # print(games_List)
