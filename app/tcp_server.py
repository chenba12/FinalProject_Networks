import sys

from scapy.arch import get_if_hwaddr

from dhcp import get_network_interface
from sql_manager import get_all, send_to_client, add_game, send_error_to_client, get_game_by_id, get_game_by_name, \
    get_games_by_platform, get_games_by_category, delete_game_by_id, get_games_by_score, get_games_by_date, \
    get_game_from_price, get_games_between_price_points, update_game, setup_db, first_setup
from message import json_to_message, error_message
import socket
import json

# This file is the TCP SERVER
# run this to start a new TCP server instance that communicate with the SQL database
# binds to ip "10.0.2.15" and port 30962

# constants
app_server_ip = "10.0.2.15"
APP_SERVER_PORT = 30961
BUFFER_SIZE = 1024


def start_server() -> None:
    f"""
    Open a tcp socket that binds 10.0.2.15 and 30962
    And listen to new client request client_socket
    """
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((app_server_ip, APP_SERVER_PORT))
    print("----------Server Details----------")
    mac_addr = get_if_hwaddr(get_network_interface())
    print("MAC address: ", mac_addr)
    print(f"IP address: {app_server_ip}")
    print(f"Port: {APP_SERVER_PORT}")
    server_socket.listen(10)
    while True:
        client_socket, address = server_socket.accept()
        print("----------New client Connected----------")
        print(f"Details: {str(address)}")
        handle_request(client_socket, address)
        client_socket.close()


def handle_request(client_socket, address) -> None:
    """
        get a request from the client and choose the matching sql method to execute based on the client request
        :param client_socket: the client socket
        :param address: the client address info
        """
    while True:
        data = client_socket.recv(BUFFER_SIZE)
        request_object = json.loads(data.decode("utf-8"))
        message_object = json_to_message(request_object)
        match str(message_object.func):
            case "getAll":
                print("----------SQL Get All----------")
                try:
                    result = get_all()
                    send_to_client(client_socket, result)
                except ValueError:
                    error_to_send = error_message("Game Catalog is empty")
                    client_socket.send(bytes(json.dumps(error_to_send), encoding="utf-8"))
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
                    send_to_client(client_socket, result)
                except ValueError:
                    send_error_to_client(client_socket, "Invalid game parameters")
            case "getGameByID":
                print("----------SQL Get Game By ID----------")
                game_id = message_object.body['id']
                try:
                    result = get_game_by_id(game_id)
                    send_to_client(client_socket, result)
                except ValueError:
                    send_error_to_client(client_socket, "Invalid game ID")
            case "getGameByName":
                print("----------SQL Get Game By Name----------")
                game_name = message_object.body['name']
                try:
                    result = get_game_by_name(game_name)
                    send_to_client(client_socket, result)
                except ValueError:
                    send_error_to_client(client_socket, "Invalid game name")
            case "getGameByPlatform":
                print("----------SQL Get Games By Platform----------")
                game_platform = message_object.body['platform']
                try:
                    result = get_games_by_platform(game_platform)
                    send_to_client(client_socket, result)
                except ValueError:
                    send_error_to_client(client_socket, "Invalid game platform")
            case "getGameByCategory":
                print("----------SQL Get Games By Category----------")
                game_category = message_object.body['category']
                try:
                    result = get_games_by_category(game_category)
                    send_to_client(client_socket, result)
                except ValueError:
                    send_error_to_client(client_socket, "Invalid game category")
            case "deleteGame":
                print("----------SQL Delete Game----------")
                game_id = message_object.body['id']
                try:
                    result = delete_game_by_id(game_id)
                    send_to_client(client_socket, result)
                except ValueError:
                    send_error_to_client(client_socket, "Invalid game ID")
            case "getGameByScore":
                print("----------SQL Get Games By Score----------")
                score = message_object.body['score']
                try:
                    result = get_games_by_score(score)
                    send_to_client(client_socket, result)
                except ValueError:
                    send_error_to_client(client_socket, "Invalid game score")
            case "getGameByYear":
                print("----------SQL Get Games By Year----------")
                release_year = message_object.body['release_year']
                try:
                    result = get_games_by_date(release_year)
                    send_to_client(client_socket, result)
                except ValueError:
                    send_error_to_client(client_socket, "Invalid game release year")
            case "getGameByPrice":
                print("----------SQL Get Games By Price----------")
                price = message_object.body['price']
                try:
                    result = get_game_from_price(price)
                    send_to_client(client_socket, result)
                except ValueError:
                    send_error_to_client(client_socket, "Invalid price range")
            case "getGameByPriceBetween":
                print("----------SQL Get Games By Price range----------")
                start = message_object.body['start']
                end = message_object.body['end']
                try:
                    result = get_games_between_price_points(start, end)
                    send_to_client(client_socket, result)
                except ValueError:
                    send_error_to_client(client_socket, "Invalid price range")
            case "updateGame":
                print("----------SQL Update Game----------")
                game_id = message_object.body['id']
                name = message_object.body['name']
                platform = message_object.body['platform']
                category = message_object.body['category']
                price = message_object.body['price']
                score = message_object.body['score']
                release_year = (message_object.body['release_year'])
                update_game(client_socket, game_id, name, platform, category, price, score, release_year)
            case "exit":
                print("----------Closing Connection----------")
                print(f"Client details:({address})")
                break
            case _:
                print("Got Invalid error")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Using default Application server IP = 10.0.2.15")
        print("Usage: sudo python3 ./app/tcp_server.py <app_server_ip>")
    else:
        app_server_ip = sys.argv[1]
        print(f"Application server IP: {app_server_ip}")
    setup_db()
    first_setup()
    print("----------TCP Server----------")
    start_server()
