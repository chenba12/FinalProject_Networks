import json
import socket

from client_sender import get_app_server_ip, get_app_server_port
from games import json_to_game, validate_platform, validate_category, validate_score, validate_year
from message import add_game_message, json_to_message, get_all_message, get_game_by_id_message, \
    get_game_by_name_message, get_game_by_platform_message, get_game_by_category_message, delete_game_message, \
    get_game_by_score_message, get_game_by_year_message, get_game_by_price_message, get_game_by_price_between_message, \
    update_game_message

BUFFER_SIZE = 8000


def tcp_connect_to_app_server():
    print("----------TCP Connection----------")
    print(f"Server details: ({get_app_server_ip()} {get_app_server_port()})")
    client_socket = socket.socket()
    client_socket.connect((get_app_server_ip(), get_app_server_port()))
    print("This is a SQL server")
    handle_request(client_socket)

    client_socket.close()  # close the connection


def handle_request(client_socket):
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
                    data = client_socket.recv(BUFFER_SIZE)
                    json_data = json.loads(data.decode("utf-8"))
                    message_object = json_to_message(json_data)
                    for item in message_object.body:
                        game = json_to_game(item)
                        print(game)
                case 2:
                    print("----------SQL Add Game----------")
                    name = input("Please enter Game Title: ")
                    platforms = validate_platform_check()
                    category = validate_category_check()
                    price = validate_price_check()
                    score = validate_score_check()
                    release_year = validate_year_check()
                    request = add_game_message(name=name, platform=platforms, category=category, price=price,
                                               score=score,
                                               release_year=release_year)
                    handle_respond(client_socket, request)
                case 3:
                    print("----------SQL Get Game By ID----------")
                    game_id = validate_id_check()
                    request = get_game_by_id_message(int(game_id))
                    handle_respond(client_socket, request)
                case 4:
                    print("----------SQL Get Game By Name----------")
                    game_name = input("Please enter Game Title: ")
                    request = get_game_by_name_message(game_name)
                    handle_respond(client_socket, request)
                case 5:
                    print("----------SQL Get Games By Platform----------")
                    platforms = validate_platform_check()
                    request = get_game_by_platform_message(platforms)
                    handle_respond(client_socket, request)
                case 6:
                    print("----------SQL Get Games By Category----------")
                    category = validate_category_check()
                    request = get_game_by_category_message(category)
                    handle_respond(client_socket, request)
                case 7:
                    print("----------SQL Delete Game----------")
                    game_id = validate_id_check()
                    request = delete_game_message(game_id)
                    handle_respond(client_socket, request)
                case 8:
                    print("----------SQL Get Games By Score----------")
                    score = validate_score_check()
                    request = get_game_by_score_message(score)
                    handle_respond(client_socket, request)
                case 9:
                    print("----------SQL Get Games By Year----------")
                    year = validate_year_check()
                    request = get_game_by_year_message(year)
                    handle_respond(client_socket, request)
                case 10:
                    print("----------SQL Get Games By Price----------")
                    price = validate_price_check()
                    request = get_game_by_price_message(price)
                    handle_respond(client_socket, request)
                    pass
                case 11:
                    print("----------SQL Get Games By Price range----------")
                    start = validate_price_check("start")
                    end = validate_price_check("end")
                    request = get_game_by_price_between_message(start, end)
                    handle_respond(client_socket, request)
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
                    handle_respond(client_socket, request)
                case 13:
                    print("Exit...")
                    break


def validate_price_check(message: str = "") -> float:
    while True:
        try:
            price = float(input(f"Please enter {message} price: "))
            break
        except ValueError:
            print("Invalid input.")
    return price


def validate_id_check() -> int:
    while True:
        try:
            game_id = int(input("Please enter Game id: "))
            break
        except ValueError:
            print("Invalid input.")
    return game_id


def validate_year_check() -> int:
    release_year = 1970
    while True:
        try:
            release_year = int(input("Please enter valid year 1970<=year<=2030: "))
        except ValueError:
            print("Invalid input.")
            continue
        if not validate_year(release_year):
            release_year = int(input("Please enter valid year 1970<=year<=2030: "))
        else:
            break
    return release_year


def validate_score_check() -> float:
    score = 0
    while True:
        try:
            score = float(input("Please valid score 0<=score<=100: "))
        except ValueError:
            print("Invalid input.")
            continue
        if not validate_score(score):
            score = float(input("Please valid score 0<=score<=100: "))
        else:
            break
    return score


def validate_category_check() -> str:
    category = input(
        "JRPG, Adventure, Shooter, Action, Fighting, Platformer, RPG, Survival, Sport, MMO: ")
    while True:
        if not validate_category(category):
            print("Please enter a valid category")
            category = input(
                "JRPG, Adventure, Shooter, Action, Fighting, Platformer, RPG, Survival, Sport, MMO: ")
        else:
            break
    return category


def validate_platform_check() -> str:
    print("Please enter a platform:")
    platforms = input("Switch, PC, Playstation5, Playstation4, Xbox series S: ")
    while True:
        if not validate_platform(platforms):
            print("Please enter a valid platform")
            platforms = input("Switch, PC, Playstation5, Playstation4, Xbox series S: ")
        else:
            break
    return platforms


def handle_respond(client_socket, request):
    client_socket.send(bytes(json.dumps(request.to_json()), encoding="utf-8"))  # send message
    data = client_socket.recv(BUFFER_SIZE)
    json_data = json.loads(data.decode("utf-8"))
    message_object = json_to_message(json_data)
    if len(message_object.body) == 0:
        print("No Game found")
    elif message_object.func == "error":
        print("No Game found")
    else:
        for item in message_object.body:
            game = json_to_game(item)
            print(game)
