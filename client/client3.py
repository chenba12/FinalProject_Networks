import socket
import pickle

from appServer import users
from message import Message
from appServer.users import Roles
import json

HOST = "127.0.0.1"


def client_program():
    client_socket = socket.socket()  # instantiate
    client_socket.connect((HOST, 65436))  # connect to the server
    request = add_user_message("123456789", "chen", "ben ami", Roles(2))
    client_socket.send(bytes(json.dumps(request.as_dict()), encoding="utf-8"))  # send message
    data = client_socket.recv(1024)  # receive response
    json_data = json.loads(data.decode("utf-8"))  # decode and load as JSON object
    user = users.json_to_user(json_data)
    print(user.__str__())
    client_socket.close()  # close the connection


def get_all_message():
    return Message("getALl", "")


def add_user_message(email, first_name, last_name, role):
    return Message("addUser", {
        'email': email,
        'last_name': last_name,
        'first_name': first_name,
    })


def delete_user_message(user_id):
    return Message("deleteUser", {
        'id': user_id
    })


if __name__ == '__main__':
    client_program()
