import message
from users import User, Base, Roles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import socket
import json

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
                result = get_all()
                for user in result:
                    print(user)
                print("Hey")
                connection.send(bytes(json.dumps(result), encoding="utf-8"))
            case "addUser":
                first_name = message_object.body["first_name"]
                last_name = message_object.body["last_name"]
                email = message_object.body["email"]
                result = add_user(email=email, last_name=last_name, first_name=first_name)
                connection.send(bytes(json.dumps(result), encoding="utf-8"))
            case _:
                print("The language doesn't matter, what matters is solving problems.")
    connection.close()  # close the connection


def setup_db():
    global factory
    engine = create_engine('sqlite:///app.db', echo=False)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    factory = session()


#
def add_user(email, last_name, first_name):
    user = User()
    user.email = email
    user.last_name = last_name
    user.first_name = first_name
    user.role = Roles(2)
    print(user)
    factory.add(user)
    factory.commit()
    print(user)
    return get_user(user.id)


def delete_user(user_id):
    result = factory.query(User).filter(User.id == user_id).first()
    if result is None:
        print(f"Can't delete user with id {user_id} nothing found")
    else:
        print(f'Deleting....')
        factory.delete(result)


def get_user(user_id):
    result = factory.query(User).filter(User.id == user_id).first()
    if result is None:
        print(f"No user with id {user_id} found")
    else:
        return result.as_dict()


def get_user_by_name(name):
    result = factory.query(User).filter(User.first_name == name).first()
    if result is None:
        print(f"No user with name {name} found")
    else:
        print(f'ID: {result.id} Email: {result.email}')


def get_all():
    result = factory.query(User).all()
    if result is not None:
        send = []
        for row in result:
            send.append(row.as_dict())
        return send
    else:
        return "The Table is Empty"


def get_clients():
    result = factory.query(User).filter(User.role == 2).all()
    for row in result:
        print(row.__str__())


if __name__ == '__main__':
    print("--- setup_db() ---")
    setup_db()
    # print("--- add_user() ---")
    # add_user()
    print("--- start_server() ---")
    start_server()
    # print("--- get_all() ---")
    # get_all()
    #
    # print("--- get_user() ---")
    # get_user(2)
    # print("--- get_user_by_name() ---")
    # get_user_by_name("Chen")
    #
    # print("--- delete_user() ---")
    # delete_user(2)
    # print("--- get_all() ---")
    # # get_all()
    # print("--- get_clients() ---")
    # get_clients()
    # print("--- add_user() ---")
    # add_user()
