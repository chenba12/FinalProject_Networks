import ast
import json
import math
import socket
import hashlib
import sys
import threading

from scapy.arch import get_if_hwaddr

from dhcp import get_network_interface
from games import json_to_game
from message import error_message, Message, result_message, str_to_message
from sql_manager import get_all, add_game, first_setup, setup_db, get_game_by_id, \
    get_game_by_name, get_games_by_platform, get_games_by_category, delete_game_by_id, get_games_by_score, \
    get_games_by_date, get_game_from_price, get_games_between_price_points, udp_update_game

# constants and globals
buffer_size = 3500
SYN = 0b00000010
SYN_ACK = 0b00000110
ACK = 0b00000001
PSH = 0b00001000
PSH_ACK = 0b00001100
FIN = 0b00000111
FIN_ACK = 0b00001001
NAK = 0b00000011
client_list = []
current_packet = []
time_out = 3
received_counter = 0
app_server_ip = "10.0.2.15"
APP_SERVER_PORT = 30961
retransmission = 0b0


# header
# | control bits (1 byte) | data size (4 bytes) | seq_number (4 bytes) | total_chunk (4 bytes) | chunk_num (4 bytes) |
# | retransmission flag (1 byte) | last chunk flag (1 byte) | | checksum (4 bytes) |
def udp_server_start():
    global buffer_size, time_out, received_counter, retransmission
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((app_server_ip, APP_SERVER_PORT))
    print("----------Server Details----------")
    mac_addr = get_if_hwaddr(get_network_interface())
    print("MAC address: ", mac_addr)
    print(f"IP address: {app_server_ip}")
    print(f"Port: {APP_SERVER_PORT}")
    print("Waiting for Clients")
    server_socket.settimeout(None)
    while True:
        # Receive packet
        received_packet, client_address = server_socket.recvfrom(buffer_size)
        received_counter += 1
        reset_timeout(server_socket)
        try:
            control_bits, data_size, seq_num, total, chunk_num, \
                retransmission_flag, last_chunk_flag, data = unpack_data(received_packet)
        except ValueError:
            print("Sending NAK")
            seq_num = int.from_bytes(received_packet[1:5], byteorder='big')
            received_packet = pack_data(NAK, seq_num, 0, 0, retransmission, 0, Message("NAK", ""))
            server_socket.sendto(received_packet, client_address)
            continue
        if client_address not in client_list:
            print(f"---------NEW Client: {client_address} seq_number={seq_num}---------")
            client_list.append(client_address)

            client_thread = threading.Thread(target=handle_client(client_address, control_bits, seq_num, server_socket))
            client_thread.start()


# header
# | control bits (1 byte) | data size (4 bytes) | seq_number (4 bytes) | chunk_num (4 bytes)
# | retransmission flag (1 byte) | last chunk flag (1 byte) | | checksum (4 bytes) |
def handle_client(client_address, control_bits, seq_num, server_socket):
    global received_counter, time_out
    client_flag = True
    if control_bits == SYN:
        server_socket.settimeout(time_out)
        seq_num += 1
        sent_packet = pack_data(SYN_ACK, seq_num, 0, 0, retransmission, 0, Message("SYN-ACK", ""))
        server_socket.sendto(sent_packet, client_address)
        server_socket.settimeout(time_out)
    while client_flag:
        try:
            sent_packet = pack_data(SYN_ACK, seq_num, 0, 0, 0, 0, Message("SYN-ACK", ""))
            server_socket.sendto(sent_packet, client_address)
            received_packet, client_address = server_socket.recvfrom(buffer_size)
        except socket.timeout:
            print(f"Timeout: {seq_num}")
            handle_timeout_error(server_socket)
            continue
        handle_recv_success(server_socket)
        try:
            control_bits, data_size, seq_num, total, chunk_num, \
                retransmission_flag, last_chunk_flag, data = unpack_data(received_packet)
            if control_bits == PSH:
                handle_psh_request(client_address, seq_num, data, server_socket)
                # uncomment to drop packets
                # if random.random() < 0.5:
                #     print("dropping...")
                #     continue
            elif control_bits == FIN:
                client_address, client_flag, control_bits, seq_num = close_client_connection(client_address,
                                                                                             client_flag,
                                                                                             control_bits, seq_num,
                                                                                             server_socket)
        except ValueError:
            sent_packet = pack_data(NAK, seq_num, 0, 0, retransmission, 0, Message("NAK", ""))
            server_socket.sendto(sent_packet, client_address)


def close_client_connection(client_address, client_flag, control_bits, seq_num, server_socket):
    """
        end of connection flow
        the client will send a FIN packet
        the server will return FIN-ACK followed by FIN-ACK from the client
        and then the collection will be closed
       :param client_address: client address
       :param client_flag:
       :param control_bits: control bits represent the type of Packet that will be sent/received
       :param seq_num: the current sequence number of the packets
       :param server_socket: the server socket
       :return: client_address, client_flag, control_bits, seq_num
       """
    global time_out, received_counter
    while client_flag:
        sent_packet = pack_data(control_bits=FIN_ACK, seq_num=seq_num, total_chunks=0, chunk_num=0,
                                retransmission_flag=retransmission, last_chunk=0, data=Message("FIN-ACK", ""))
        server_socket.sendto(sent_packet, client_address)
        try:
            received_packet, client_address = server_socket.recvfrom(buffer_size)
        except socket.timeout:
            print(f"Timeout: seq_num={seq_num}")
            handle_timeout_error(server_socket)
            continue
        handle_recv_success(server_socket)
        try:
            control_bits, data_size, seq_num, total, chunk_num, \
                retransmission_flag, last_chunk_flag, data = unpack_data(received_packet)
        except ValueError:
            sent_packet = pack_data(NAK, seq_num, 0, 0, retransmission, 0, Message("NAK", ""))
            server_socket.sendto(sent_packet, client_address)
        if control_bits == FIN_ACK:
            print(f"---------Closing communication with: {client_address}---------")
            client_flag = False
            server_socket.settimeout(None)
            client_list.remove(client_address)
            break
    return client_address, client_flag, control_bits, seq_num


def handle_psh_request(client_address, seq_num, data: Message, server_socket) -> None:
    """
    This method handles the PSH requests get the data from the database and send it back to the user
    :param client_address: client ip and port
    :param seq_num: the current sequence number
    :param data: the data received from the packet
    :param server_socket: the server socket
    :return: the current sequence number
    """
    server_socket.settimeout(5)
    match str(data.func):
        case "getAll":
            print("----------SQL Get All----------")
            try:
                result = get_all()
                seq_num_r = send_to_chunks(client_address, seq_num, result, server_socket)
                seq_num = seq_num_r
            except ValueError:
                error_to_send = error_message("Game Catalog is empty")
                server_socket.send(bytes(json.dumps(error_to_send), encoding="utf-8"))
        case "addGame":
            print("----------SQL Add Game----------")
            dict_obj = ast.literal_eval(data.body)
            game = json_to_game(dict_obj)
            name = game.name
            platform = game.platform
            category = game.category
            price = game.price
            release_year = game.release_year
            score = game.score

            try:
                result = add_game(name=name, category=category, platform=platform, price=price,
                                  score=score, release_year=release_year)
                seq_num_r = send_to_chunks(client_address, seq_num, result, server_socket)
                seq_num = seq_num_r
            except ValueError:
                pass
        case "getGameByID":
            print("----------SQL Get Game By ID----------")
            dict_obj = ast.literal_eval(data.body)
            game_id = dict_obj['id']
            try:
                result = get_game_by_id(game_id)
                seq_num_r = send_to_chunks(client_address, seq_num, result, server_socket)
                seq_num = seq_num_r
            except ValueError:
                pass
        case "getGameByName":
            print("----------SQL Get Game By Name----------")
            dict_obj = ast.literal_eval(data.body)
            game_name = dict_obj['name']
            try:
                result = get_game_by_name(game_name)
                seq_num_r = send_to_chunks(client_address, seq_num, result, server_socket)
                seq_num = seq_num_r
            except ValueError:
                pass
        case "getGameByPlatform":
            print("----------SQL Get Games By Platform----------")
            dict_obj = ast.literal_eval(data.body)
            game_platform = dict_obj['platform']
            try:
                result = get_games_by_platform(game_platform)
                seq_num_r = send_to_chunks(client_address, seq_num, result, server_socket)
                seq_num = seq_num_r
            except ValueError:
                pass
        case "getGameByCategory":
            print("----------SQL Get Games By Category----------")
            dict_obj = ast.literal_eval(data.body)
            game_category = dict_obj['category']
            try:
                result = get_games_by_category(game_category)
                seq_num_r = send_to_chunks(client_address, seq_num, result, server_socket)
                seq_num = seq_num_r
            except ValueError:
                pass
        case "deleteGame":
            print("----------SQL Delete Game----------")
            dict_obj = ast.literal_eval(data.body)
            game_id = dict_obj['id']
            try:
                result = delete_game_by_id(game_id)
                seq_num_r = send_to_chunks(client_address, seq_num, result, server_socket)
                seq_num = seq_num_r
            except ValueError:
                pass
        case "getGameByScore":
            print("----------SQL Get Games By Score----------")
            dict_obj = ast.literal_eval(data.body)
            score = dict_obj['score']
            try:
                result = get_games_by_score(score)
                seq_num_r = send_to_chunks(client_address, seq_num, result, server_socket)
                seq_num = seq_num_r
            except ValueError:
                pass
        case "getGameByYear":
            print("----------SQL Get Games By Year----------")
            dict_obj = ast.literal_eval(data.body)
            release_year = dict_obj['release_year']
            try:
                result = get_games_by_date(release_year)
                seq_num_r = send_to_chunks(client_address, seq_num, result, server_socket)
                seq_num = seq_num_r
            except ValueError:
                pass
        case "getGameByPrice":
            print("----------SQL Get Games By Price----------")
            dict_obj = ast.literal_eval(data.body)
            price = dict_obj['price']
            try:
                result = get_game_from_price(price)
                seq_num_r = send_to_chunks(client_address, seq_num, result, server_socket)
                seq_num = seq_num_r
            except ValueError:
                pass
        case "getGameByPriceBetween":
            print("----------SQL Get Games By Price range----------")
            dict_obj = ast.literal_eval(data.body)
            start = dict_obj['start']
            end = dict_obj['end']
            try:
                result = get_games_between_price_points(start, end)
                seq_num_r = send_to_chunks(client_address, seq_num, result, server_socket)
                seq_num = seq_num_r
            except ValueError:
                pass
        case "updateGame":
            print("----------SQL Update Game----------")
            dict_obj = ast.literal_eval(data.body)
            game = json_to_game(dict_obj)
            game_id = game.id
            name = game.name
            platform = game.platform
            category = game.category
            price = game.price
            release_year = game.release_year
            score = game.score
            result = udp_update_game(game_id, name, platform, category, price, release_year, score)
            seq_num_r = send_to_chunks(client_address, seq_num, result, server_socket)
            seq_num = seq_num_r
        case _:
            print("Got Invalid error")
    return seq_num


def send_to_chunks(client_address, seq_num, result, server_socket):
    """
       This method handles sending the chunks of the data that fit the current buffer size to the client
       while also waiting for ack on each of them
       :param client_address: the client ip and port
       :param seq_num: the current sequence number
       :param result: the result of the SQL query
       :param server_socket: the server socket
       :return: the current sequence number
       """
    global time_out, received_counter
    chunks = slice_data(result)
    size = len(chunks)
    i = 1
    for chunk in chunks:
        if size - i == 0:
            last_chunk = 1
        else:
            last_chunk = 0

        waiting_for_ack = True
        while waiting_for_ack:
            try:
                sent_packet = pack_data(control_bits=PSH_ACK, seq_num=seq_num, total_chunks=size,
                                        chunk_num=size - i,
                                        retransmission_flag=retransmission, last_chunk=last_chunk,
                                        data=result_message(chunk))
                server_socket.sendto(sent_packet, client_address)
                received_packet, client_address = server_socket.recvfrom(buffer_size)
            except socket.timeout:
                print(f"timeout {seq_num}")
                handle_timeout_error(server_socket)
                continue
            handle_recv_success(server_socket)
            try:
                control_bits, data_size, seq_num, total, chunk_num, \
                    retransmission_flag, last_chunk_flag, data = unpack_data(received_packet)
                if control_bits == ACK:
                    waiting_for_ack = False
            except ValueError:
                sent_packet = pack_data(NAK, seq_num, 0, 0, retransmission, 0, Message("NAK", ""))
                server_socket.sendto(sent_packet, client_address)
        i += 1
    return seq_num


def bits_to_string(control_bits_bytes):
    """
    :param control_bits_bytes: control bits represent the type of Packet that will be sent/received
    :return: String name of the control bits
    """
    if control_bits_bytes == SYN:
        return "SYN"
    elif control_bits_bytes == SYN_ACK:
        return "SYN_ACK"
    elif control_bits_bytes == PSH:
        return "PSH"
    elif control_bits_bytes == PSH_ACK:
        return "PSH_ACK"
    elif control_bits_bytes == ACK:
        return "ACK"
    elif control_bits_bytes == FIN:
        return "FIN"
    elif control_bits_bytes == FIN_ACK:
        return "FIN_ACK"
    elif control_bits_bytes == NAK:
        return "NAK"
    else:
        print("UNKNOWN")


def pack_data(control_bits, seq_num, total_chunks, chunk_num, retransmission_flag, last_chunk, data: Message):
    """
    This method packs the data to make it ready to be sent to the receiving end includes the header and the data itself
    :param control_bits: control bits represent the type of Packet that will be sent
    :param seq_num: the current sequence number
    :param total_chunks: the number of chunks that will be sent
    :param chunk_num: current chunk
    :param retransmission_flag: ask for retransmission true/false
    :param last_chunk: last chunk true/false
    :param data: the data/chunk
    :return: a packet ready to be sent
    """
    control_bits_bytes = control_bits.to_bytes(1, byteorder='big')
    data_size_bytes = data.get_len().to_bytes(4, byteorder='big')
    seq_num_bytes = seq_num.to_bytes(4, byteorder='big')
    total_chunks_bytes = total_chunks.to_bytes(4, byteorder='big')
    chunk_num_bytes = chunk_num.to_bytes(4, byteorder='big')
    retransmission_flag = retransmission_flag.to_bytes(1, byteorder='big')
    last_chunk_flag = last_chunk.to_bytes(1, byteorder='big')
    header = control_bits_bytes + data_size_bytes + seq_num_bytes + total_chunks_bytes \
             + chunk_num_bytes + retransmission_flag + last_chunk_flag
    checksum = hashlib.sha256(header).digest()[:4]
    data_bytes = data.__str__().encode('utf-8')
    packet = header + checksum + data_bytes
    # uncomment to make faulty check_sum
    # if random.random() < 0.1:
    #     # introduce random error in checksum
    #     i = random.randint(0, 3)
    #     checksum = checksum[:i] + bytes([checksum[i] ^ 0xFF]) + checksum[i + 1:]
    print("--------------Sent packet--------------")
    print(f"Details: Control_bits:{bits_to_string(control_bits)},Seq:{seq_num},Total:{total_chunks}")
    print(f"Chunk:{chunk_num} Data_size:{data.get_len()} Retransmission:{retransmission_flag} "
          f"Last_chunk:{last_chunk}")
    print(f"Data:{len(packet)}")
    return packet


def unpack_data(packet):
    """
    Unpack the data
    Get the header from bits to control_bits, data_size, seq_num,
    total, chunk_num, retransmission_flag, last_chunk_flag
    :param packet: the packet that was received from the sender
    :return: control_bits, data_size, seq_num, total, chunk_num, retransmission_flag, last_chunk_flag,
    message_object
    """
    control_bits = int.from_bytes(packet[:1], byteorder='big')
    data_size = int.from_bytes(packet[1:5], byteorder='big')
    seq_num = int.from_bytes(packet[5:9], byteorder='big')
    total = int.from_bytes(packet[9:13], byteorder='big')
    chunk_num = int.from_bytes(packet[13:17], byteorder='big')
    retransmission_flag = int.from_bytes(packet[17:18], byteorder='big')
    last_chunk_flag = int.from_bytes(packet[18:19], byteorder='big')
    checksum = packet[19:23]
    data = packet[23:]
    message_object = str_to_message(data.decode())
    # Compute checksum over the received packet (excluding the checksum field)
    header = packet[:19]
    computed_checksum = hashlib.sha256(header).digest()[:4]
    # Verify the checksum
    if checksum != computed_checksum:
        raise ValueError('Packet has been corrupted')
    print("------------Received packet------------")
    print(f"Details: control_bits:{bits_to_string(control_bits)},seq:{seq_num},chunk:{chunk_num}")
    print(
        f"data_size:{len(packet)} retransmission:{retransmission_flag} last_chunk:{last_chunk_flag}")
    print(f"data:{message_object}")
    print("---------------------------------------")
    return control_bits, data_size, seq_num, total, chunk_num, retransmission_flag, last_chunk_flag, message_object


def handle_buffer():
    """
    Update the global buffer size variable based on the amount
    """
    global buffer_size, received_counter
    if received_counter == 0 and buffer_size >= 450:
        buffer_size = int(buffer_size / 2)
    if buffer_size != 3500 and received_counter > 1:
        buffer_size = int(buffer_size * 2)


def slice_data(data):
    """
    slice the full data from the sql server into a smaller chunks based on the buffered size
    :param data: the data to be sent
    :return: chunks array
    """
    global buffer_size
    # header size
    header_size = 23

    # Convert the data to a JSON string
    json_data = json.dumps(data)

    # Calculate the number of chunks
    num_chunks = math.ceil(len(json_data) / (buffer_size - header_size))

    # Slice the JSON data into chunks
    chunks = []
    for i in range(num_chunks):
        chunk_start = i * (buffer_size - header_size)
        chunk_end = (i + 1) * (buffer_size - header_size)
        chunk = json_data[chunk_start:chunk_end]
        chunks.append(chunk)

    return chunks


def concatenate_chunks(chunks):
    """
    :param chunks: the array of chunks representing the full data
    :return: get a string of the full data
    """
    data = "".join(chunks)
    return data


def reset_timeout(server_socket):
    global time_out
    if received_counter > 1:
        time_out = 3
        server_socket.settimeout(time_out)


def handle_recv_success(current_socket):
    global received_counter, retransmission
    received_counter += 1
    retransmission = 0
    reset_timeout(current_socket)


def handle_timeout_error(current_socket):
    global time_out, received_counter, retransmission
    time_out += 1
    current_socket.settimeout(time_out)
    received_counter = 0
    handle_buffer()
    retransmission = 0b1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Using default Application server IP = 10.0.2.15")
        print("Usage: sudo python3 ./app/tcp_server.py <app_server_ip>")
    else:
        app_server_ip = sys.argv[1]
        print(f"Application server IP: {app_server_ip}")
    setup_db()
    first_setup()
    print("----------RUDP Server----------")
    udp_server_start()
