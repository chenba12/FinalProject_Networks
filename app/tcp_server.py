from sql_manager import get_all, send_to_client, add_game, send_error_to_client, get_game_by_id, get_game_by_name, \
    get_games_by_platform, get_games_by_category, delete_game_by_id, get_games_by_score, get_games_by_date, \
    get_game_from_price, get_games_between_price_points, update_game, setup_db, first_setup
from message import json_to_message, error_message
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
    print("----------New client Connected----------")
    print(f"Details: {str(address)}")
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


# Main to test some methods
if __name__ == '__main__':
    setup_db()
    first_setup()
    print("----------TCP Server----------")
    start_server()
