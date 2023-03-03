import socket
import pickle

from message import Message, add_game_message
from appServer.games import json_to_game
import json

HOST = "127.0.0.1"


def client_program():
    client_socket = socket.socket()  # instantiate
    client_socket.connect((HOST, 65436))  # connect to the server
    request = add_game_message("123456789", "chen", "ben ami")
    client_socket.send(bytes(json.dumps(request.as_dict()), encoding="utf-8"))  # send message
    data = client_socket.recv(1024)  # receive response
    json_data = json.loads(data.decode("utf-8"))  # decode and load as JSON object
    game = json_to_game(json_data)
    print(game.__str__())
    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()
