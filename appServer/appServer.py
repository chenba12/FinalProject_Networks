import message
from games import Game, Base, validate_platform, validate_year, validate_category, validate_score
from sqlalchemy import create_engine, and_, literal
from sqlalchemy.orm import sessionmaker
import socket
import json
import datetime

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65436  # Port to listen on (non-privileged ports are > 1023)


def start_server() -> None:
    server_socket = socket.socket()  # get instance
    server_socket.bind((HOST, PORT))  # bind host address and port together
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.listen(10)
    connection, address = server_socket.accept()  # accept new connection

    print("Connection from: " + str(address))
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = connection.recv(1024)
        if not data:
            break
        request_object = json.loads(data.decode("utf-8"))
        message_object = message.json_to_message(request_object)
        match str(message_object.func):
            case "getAll":
                try:
                    result = get_all()
                    send_to_client(connection, result)
                except ValueError:
                    error_message = message.error_message("Game Catalog is empty")
                    connection.send(bytes(json.dumps(error_message), encoding="utf-8"))
            case "addGame":
                name = message_object.body['name'],
                platform = message_object.body['platform'],
                category = message_object.body['category'],
                price = message_object.body['price'],
                release_year = (message_object.body['release_year'])
                score = message_object.body['score']
                try:
                    result = add_game(name=name, category=category, platform=platform, price=price,
                                      score=score, release_year=release_year)
                    send_to_client(connection, result)
                except ValueError:
                    error_message = message.error_message("Invalid game parameters")
                    connection.send(bytes(json.dumps(error_message), encoding="utf-8"))
            case "getGameByID":
                game_id = message_object.body['id']
                try:
                    result = get_game_by_id(game_id)
                    send_to_client(connection, result)
                except ValueError:
                    error_message = message.error_message("Invalid game ID")
                    connection.send(bytes(json.dumps(error_message), encoding="utf-8"))
            case "getGameByName":
                game_name = message_object.body['name']
                try:
                    result = get_game_by_name(game_name)
                    send_to_client(connection, result)
                except ValueError:
                    error_message = message.error_message("Invalid game name")
                connection.send(bytes(json.dumps(error_message), encoding="utf-8"))
            case "getGameByPlatform":
                game_name = message_object.body['platform']
                try:
                    result = get_game_by_name(game_name)
                    send_to_client(connection, result)
                except ValueError:
                    error_message = message.error_message("Invalid game platform")
                    connection.send(bytes(json.dumps(error_message), encoding="utf-8"))
            case "getGameByCategory":
                game_category = message_object.body['category']
                try:
                    result = get_games_by_category(game_category)
                    send_to_client(connection, result)
                except ValueError:
                    error_message = message.error_message("Invalid game category")
                    connection.send(bytes(json.dumps(error_message), encoding="utf-8"))
            case "deleteGame":
                game_id = message_object.body['id']
                try:
                    result = delete_game_by_id(game_id)
                    send_to_client(connection, result)
                except ValueError:
                    error_message = message.error_message("Invalid game ID")
                    connection.send(bytes(json.dumps(error_message), encoding="utf-8"))
            case "getGameByScore":
                score = message_object.body['score']
                try:
                    result = get_games_by_score(score)
                    send_to_client(connection, result)
                except ValueError:
                    error_message = message.error_message("Invalid score")
                    connection.send(bytes(json.dumps(error_message), encoding="utf-8"))
            case "getGameByYear":
                release_year = message_object.body['release_year']
                try:
                    result = get_games_by_date(release_year)
                    send_to_client(connection, result)
                except ValueError:
                    error_message = message.error_message("Invalid Year")
                    connection.send(bytes(json.dumps(error_message), encoding="utf-8"))
            case "getGameByPrice":
                price = message_object.body['price']
                try:
                    result = get_game_from_price(price)
                    send_to_client(connection, result)
                except ValueError:
                    error_message = message.error_message("Invalid Price range")
                    connection.send(bytes(json.dumps(error_message), encoding="utf-8"))
            case "getGameByPriceBetween":
                start = message_object.body['start']
                end = message_object.body['end']
                try:
                    result = get_games_between_price_points(start, end)
                    send_to_client(connection, result)
                except ValueError:
                    error_message = message.error_message("Invalid Price range")
                    connection.send(bytes(json.dumps(error_message), encoding="utf-8"))
            case _:
                print("Got Invalid error")
    connection.close()  # close the connection


def send_to_client(connection, result):
    message_to_send = message.result_message(result)
    connection.send(bytes(json.dumps(message_to_send), encoding="utf-8"))


def setup_db() -> None:
    global factory
    engine = create_engine('sqlite:///app.db', echo=False)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    factory = session()


def get_all():
    result = factory.query(Game).all()
    if result is not None:
        send = []
        for game in result:
            send.append(game.as_dict())
        if not send:
            raise ValueError("The Table is Empty")
        else:
            return send


def add_game(name, platform, category, price, score, release_year):
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
        factory.add(game)
        factory.commit()
        print(game)
        return get_game_by_id(game.id)
    else:
        raise ValueError("Value Error")


def delete_game_by_id(game_id):
    result = factory.query(Game).filter(Game.id == game_id).first()
    if result is None:
        raise ValueError(f"Can't delete game with id {game_id} nothing found")
    else:
        print(f'Deleting....')
        factory.delete(result)
        return "Success"


def get_game_by_id(game_id):
    result = factory.query(Game).filter(Game.id == game_id).first()
    if result is None:
        raise ValueError(f"No game with id {game_id} found")
    else:
        return result.as_dict()


def get_game_by_name(name):
    result = factory.query(Game).filter(Game.name.like(f'{name}%')).all()
    if result is not None:
        send = []
        for game in result:
            send.append(game.as_dict())
        if not send:
            raise ValueError("No game found with that name")
        else:
            return send


def get_game_from_price(price):
    result = factory.query(Game).filter(Game.price >= price).all()
    if result is not None:
        send = []
        for game in result:
            send.append(game.as_dict())
        if not send:
            raise ValueError(f"No games with price greater or equal to {price}")
        else:
            return send


def get_games_by_category(category):
    result = factory.query(Game).filter(Game.price == category)
    if result is not None:
        send = []
        for game in result:
            send.append(game.as_dict())
        if not send:
            raise ValueError(f"No games from category: {category}")
        else:
            return send


def get_games_by_platform(platform):
    if validate_platform(platform):
        result = factory.query(Game).filter(Game.platform == platform).all()
        if result is not None:
            send = []
            for game in result:
                send.append(game.as_dict())
            if not send:
                raise ValueError(f"No games from platform: {platform}")
            else:
                return send
    raise ValueError("not a valid platform")


def get_games_between_price_points(start, end):
    if start > end:
        raise ValueError("start price can't be larger than end price")
    result = factory.query(Game).filter(and_(Game.price >= start, Game.price <= end)).all()
    if result is not None:
        send = []
        for game in result:
            send.append(game.as_dict())
        if not send:
            raise ValueError(f"No games with price range from {start} to {end}")
        else:
            return send


def get_games_by_date(release_year):
    validate_year(release_year)
    result = factory.query(Game).filter(Game.release_year == release_year).all()
    if result is not None:
        send = []
        for game in result:
            send.append(game.as_dict())
        if not send:
            raise ValueError(f"No games from year: {release_year}")
        else:
            return send


def get_games_by_score(score):
    validate_score(score)
    result = factory.query(Game).filter(Game.score == score).all()
    if result is not None:
        send = []
        for game in result:
            send.append(game.as_dict())
        if not send:
            raise ValueError(f"No games with score: {score}")
        else:
            return send


def first_setup():
    try:
        get_all()
    except ValueError:
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


if __name__ == '__main__':
    print("--- setup_db() ---")
    setup_db()
    print("--- first_setup() ---")
    first_setup()
    # print("--- add_game() ---")
    # add_game()
    # print("--- start_server() ---")
    # start_server()
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
