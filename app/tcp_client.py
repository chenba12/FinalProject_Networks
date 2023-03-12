import json
import socket

from client_sender import get_app_server_ip, get_app_server_port, validate_id_check, validate_platform_check, \
    validate_category_check, validate_price_check, validate_score_check, validate_year_check, validate_name_check, \
    validate_price_range_check
from games import json_to_game
from message import add_game_message, json_to_message, get_all_message, get_game_by_id_message, \
    get_game_by_name_message, get_game_by_platform_message, get_game_by_category_message, delete_game_message, \
    get_game_by_score_message, get_game_by_year_message, get_game_by_price_message, get_game_by_price_between_message, \
    update_game_message, exit_message

# This file handles the TCP client methods
# connects to the Application server TCP socket
# Send request to get data from the Application server
BUFFER_SIZE = 1024


def tcp_connect_to_app_server(client_ip):
    """
    Open TCP socket in order to connect to the Application server TCP socket
    """
    print("----------TCP Connection----------")
    print(f"Server details: ({get_app_server_ip()}:{get_app_server_port()})")
    if client_ip == '':
        print(f"Client details: (localhost:20961)")
    else:
        print(f"Client details: ({client_ip}:20961)")
    client_socket = socket.socket()
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.bind((client_ip, 20961))
    client_socket.connect((get_app_server_ip(), get_app_server_port()))
    print("This is a SQL server")
    handle_request(client_socket)
    client_socket.close()


# sudo ip addr add 192.168.1.100/24 dev enp0s3


def handle_request(client_socket):
    """
    This method is getting user input about which data the user want to send over to the server
    and then get a response
    :param client_socket: the TCP client socket
    """
    running = True
    while running:
        print("The following methods are available")
        print("Enter the number of the method you want")
        print("(1: Get all) (2:Add Game) (3:Get Game By ID) (4:Search Game) (5:Get Games By Platform)")
        print(
            "(6: Get Games By Category) (7:Delete Game) (8:Get Games By Score) (9:Get Games By Year)")
        print("(10:Get Games By Price) (11:Get Game By Price Between) (12:Update Game) (13:Exit)")
        user_input = input()
        if 13 < int(user_input) or int(user_input) < 1:
            print("Invalid choice")
            continue
        else:
            match int(user_input):
                case 1:
                    print("----------SQL Get All----------")
                    request = get_all_message()
                    client_socket.send(bytes(json.dumps(request.to_json()), encoding="utf-8"))  # send message
                    data = recv_from_server(client_socket)
                    json_obj = json.loads(data)
                    message_obj = json_to_message(json_obj)
                    for item in message_obj.body:
                        game = json_to_game(item)
                        print(game)
                case 2:
                    print("----------SQL Add Game----------")
                    game_name = validate_name_check()
                    platforms = validate_platform_check()
                    category = validate_category_check()
                    price = validate_price_check()
                    score = validate_score_check()
                    release_year = validate_year_check()
                    request = add_game_message(name=game_name, platform=platforms, category=category, price=price,
                                               score=score,
                                               release_year=release_year)
                    tcp_handle_respond(client_socket, request)
                case 3:
                    print("----------SQL Get Game By ID----------")
                    game_id = validate_id_check()
                    request = get_game_by_id_message(int(game_id))
                    tcp_handle_respond(client_socket, request)
                case 4:
                    print("----------SQL Get Game By Name----------")
                    game_name = validate_name_check()
                    request = get_game_by_name_message(game_name)
                    tcp_handle_respond(client_socket, request)
                case 5:
                    print("----------SQL Get Games By Platform----------")
                    platforms = validate_platform_check()
                    request = get_game_by_platform_message(platforms)
                    tcp_handle_respond(client_socket, request)
                case 6:
                    print("----------SQL Get Games By Category----------")
                    category = validate_category_check()
                    request = get_game_by_category_message(category)
                    tcp_handle_respond(client_socket, request)
                case 7:
                    print("----------SQL Delete Game----------")
                    game_id = validate_id_check()
                    request = delete_game_message(game_id)
                    tcp_handle_respond(client_socket, request)
                case 8:
                    print("----------SQL Get Games By Score----------")
                    score = validate_score_check()
                    request = get_game_by_score_message(score)
                    tcp_handle_respond(client_socket, request)
                case 9:
                    print("----------SQL Get Games By Year----------")
                    year = validate_year_check()
                    request = get_game_by_year_message(year)
                    tcp_handle_respond(client_socket, request)
                case 10:
                    print("----------SQL Get Games By Price----------")
                    price = validate_price_check()
                    request = get_game_by_price_message(price)
                    tcp_handle_respond(client_socket, request)
                    pass
                case 11:
                    print("----------SQL Get Games By Price range----------")
                    start, end = validate_price_range_check()
                    request = get_game_by_price_between_message(start, end)
                    tcp_handle_respond(client_socket, request)
                case 12:
                    print("----------SQL Update Game----------")
                    game_id = validate_id_check()
                    name = input("Please enter Game Title: ")
                    platforms = validate_platform_check()
                    category = validate_category_check()
                    price = validate_price_check()
                    score = validate_score_check()
                    release_year = validate_year_check()
                    request = update_game_message(game_id, name, platforms, category, price, score, release_year)
                    tcp_handle_respond(client_socket, request)
                case 13:
                    print("Exit...")
                    request = exit_message()
                    client_socket.send(bytes(json.dumps(request.to_json()), encoding="utf-8"))
                    break


def recv_from_server(sock):
    received_data = b''
    while True:
        chunk = sock.recv(BUFFER_SIZE)
        if not chunk:
            return received_data.decode()
        received_data += chunk
        if len(chunk) < BUFFER_SIZE:
            return received_data.decode()


def tcp_handle_respond(client_socket, request):
    """
    handles the response from the server send the data over as json and this method convert it to Message class obj
    and get the data from there
    :param client_socket: the TCP client socket
    :param request: The request that the user wanted to send to the server
    """
    client_socket.send(bytes(json.dumps(request.to_json()), encoding="utf-8"))  # send message
    data = recv_from_server(client_socket)
    json_data = json.loads(data)
    message_object = json_to_message(json_data)
    if len(message_object.body) == 0:
        print("No Game found")
    elif message_object.func == "error":
        print("No Game found")
    else:
        for item in message_object.body:
            game = json_to_game(item)
            print(game)
