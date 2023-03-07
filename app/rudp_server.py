import ast
import json
import math
import socket
import hashlib
import threading

from games import json_to_game
from message import error_message, Message, json_to_message, result_message, str_to_message
from sql_manager import get_all, add_game, send_to_client, first_setup, setup_db, send_error_to_client, get_game_by_id, \
    get_game_by_name, get_games_by_platform, get_games_by_category, delete_game_by_id, get_games_by_score, \
    get_games_by_date, get_game_from_price, get_games_between_price_points, udp_update_game

# constants
buffer_size = 1024
SYN = 0b00000010
SYN_ACK = 0b00000100
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


# header
# | control bits (1 byte) | data size (4 bytes) | seq_number (4 bytes) | total_chunk (4 bytes) | chunk_num (4 bytes)
# | retransmission flag (1 byte) | last chunk flag (1 byte) | | checksum (4 bytes) |
def udp_server_start():
    global buffer_size, time_out, received_counter
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 8000))
    print("Waiting for Clients")
    while True:
        # Receive packet
        try:
            received_packet, client_address = server_socket.recvfrom(buffer_size)
        except socket.timeout:
            time_out += 1
            server_socket.settimeout(time_out)
            received_counter = 0
            handle_buffer()
            continue
        received_counter += 1
        reset_timeout(server_socket)
        try:
            control_bits, data_size, seq_num, total, chunk_num, retransmission_flag, last_chunk_flag, data = unpack_data(
                received_packet)
        except ValueError:
            print("Sending NAK")
            seq_num = int.from_bytes(received_packet[1:5], byteorder='big')
            received_packet = pack_data(NAK, seq_num, 0, 0, 0, 0, Message("NAK", ""))
            server_socket.sendto(received_packet, client_address)
            continue
        if client_address not in client_list:
            print(f"---------NEW Client: {client_address} seq_number={seq_num}---------")
            client_list.append(client_address)
            client_thread = threading.Thread(
                target=handle(client_address, control_bits, seq_num, server_socket))
            client_thread.start()


# header
# | control bits (1 byte) | data size (4 bytes) | seq_number (4 bytes) | chunk_num (4 bytes)
# | retransmission flag (1 byte) | last chunk flag (1 byte) | | checksum (4 bytes) |
def handle(client_address, control_bits, seq_num, server_socket):
    global received_counter, time_out
    client_flag = True
    if control_bits == SYN:
        server_socket.settimeout(time_out)
        seq_num += 1
        sent_packet = pack_data(SYN_ACK, seq_num, 0, 0, 0, 0, Message("SYN-ACK", ""))
        server_socket.sendto(sent_packet, client_address)
        server_socket.settimeout(None)
    elif control_bits == NAK:
        print("SYN-ACK")
        sent_packet = pack_data(SYN_ACK, seq_num, 0, 0, 0, 0, Message("SYN-ACK", ""))
        server_socket.sendto(sent_packet, client_address)
    while client_flag:
        try:
            received_packet, client_address = server_socket.recvfrom(buffer_size)
        except socket.timeout:
            print(f"Timeout: {seq_num}")
            sent_packet = pack_data(SYN_ACK, seq_num, 0, 0, 0, 0, Message("SYN-ACK", ""))
            server_socket.sendto(sent_packet, client_address)
            time_out += 1
            server_socket.settimeout(time_out)
            received_counter = 0
            handle_buffer()
            continue
        received_counter += 1
        reset_timeout(server_socket)
        try:
            control_bits, data_size, seq_num, total, chunk_num, \
                retransmission_flag, last_chunk_flag, data = unpack_data(received_packet)
            if control_bits == PSH:
                print("GOT PUSH")
                # TODO uncomment to drop packets
                handle_request(client_address, seq_num, data, server_socket)
                # if random.random() < 0.5:
                #     print("dropping...")
                #     continue
            elif control_bits == FIN:
                client_address, client_flag, control_bits, seq_num = close_client_connection(client_address,
                                                                                             client_flag,
                                                                                             control_bits, seq_num,
                                                                                             server_socket)
        except ValueError:
            print("am i here?")
            sent_packet = pack_data(NAK, seq_num, 0, 0, 0, 0, Message("NAK", ""))
            server_socket.sendto(sent_packet, client_address)


def send_to_chunks(client_address, seq_num, result, server_socket):
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
                                        retransmission=0, last_chunk=last_chunk, data=result_message(chunk))
                server_socket.sendto(sent_packet, client_address)
                received_packet, client_address = server_socket.recvfrom(buffer_size)
            except socket.timeout:
                # TODO check this
                print(f"timeout {seq_num} :(")
                time_out += 1
                server_socket.settimeout(time_out)
                received_counter = 0
                handle_buffer()
                continue
            received_counter += 1
            reset_timeout(server_socket)
            try:
                control_bits, data_size, seq_num, total, chunk_num, \
                    retransmission_flag, last_chunk_flag, data = unpack_data(received_packet)
                if control_bits == ACK:
                    print("GOT ACK can send more chunks")
                    waiting_for_ack = False
            except ValueError:
                print("inside send chunks")
                sent_packet = pack_data(NAK, seq_num, 0, 0, 0, 0, Message("NAK", ""))
                server_socket.sendto(sent_packet, client_address)
        i += 1
    return seq_num


def close_client_connection(client_address, client_flag, control_bits, seq_num, server_socket):
    global time_out, received_counter
    while client_flag:
        sent_packet = pack_data(control_bits=FIN_ACK, seq_num=seq_num, total_chunks=0, chunk_num=0,
                                retransmission=0, last_chunk=0, data=Message("FIN-ACK", ""))
        server_socket.sendto(sent_packet, client_address)
        try:
            received_packet, client_address = server_socket.recvfrom(buffer_size)
        except socket.timeout:
            print(f"Timeout: seq_num={seq_num}")
            sent_packet = pack_data(FIN_ACK, seq_num, 0, 0, 0, 0, Message("FIN-ACK", ""))
            server_socket.sendto(sent_packet, client_address)
            time_out += 1
            server_socket.settimeout(time_out)
            received_counter = 0
            handle_buffer()
            continue
        received_counter += 1
        reset_timeout(server_socket)
        try:
            control_bits, data_size, seq_num, total, chunk_num, \
                retransmission_flag, last_chunk_flag, data = unpack_data(received_packet)
        except ValueError:
            sent_packet = pack_data(NAK, seq_num, 0, 0, 0, 0, Message("NAK", ""))
            server_socket.sendto(sent_packet, client_address)
        if control_bits == FIN_ACK:
            print(f"---------Closing communication with: {client_address}---------")
            client_flag = False
            server_socket.settimeout(None)
            client_list.remove(client_address)
            break
    return client_address, client_flag, control_bits, seq_num


def handle_request(client_address, seq_num, data: Message, server_socket) -> None:
    server_socket.timeout(5)
    match str(data.func):
        case "getAll":
            print("----------SQL Get All----------")
            try:
                result = get_all()
                seq_num_r = send_to_chunks(client_address, seq_num, result, server_socket)
                seq_num = seq_num_r
            except ValueError:
                # TODO check those
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


def pack_data(control_bits, seq_num, total_chunks, chunk_num, retransmission, last_chunk, data: Message):
    control_bits_bytes = control_bits.to_bytes(1, byteorder='big')
    data_size_bytes = len(data.to_json()).to_bytes(4, byteorder='big')
    seq_num_bytes = seq_num.to_bytes(4, byteorder='big')
    total_chunks_bytes = total_chunks.to_bytes(4, byteorder='big')
    chunk_num_bytes = chunk_num.to_bytes(4, byteorder='big')
    retransmission_flag = retransmission.to_bytes(1, byteorder='big')
    last_chunk_flag = last_chunk.to_bytes(1, byteorder='big')
    header = control_bits_bytes + data_size_bytes + seq_num_bytes + total_chunks_bytes \
             + chunk_num_bytes + retransmission_flag + last_chunk_flag
    checksum = hashlib.sha256(header).digest()[:4]
    data_bytes = data.__str__().encode('utf-8')
    packet = header + checksum + data_bytes
    # TODO uncomment to make faulty check_sum
    # if random.random() < 0.1:
    #     # introduce random error in checksum
    #     i = random.randint(0, 3)
    #     checksum = checksum[:i] + bytes([checksum[i] ^ 0xFF]) + checksum[i + 1:]
    print("--------------Sent packet--------------")
    print(f"Details: Control_bits:{get_bits(control_bits)},Seq:{seq_num},Total:{total_chunks}")
    print(f"Chunk:{chunk_num} Data_size:{len(data.to_json())} Retransmission:{retransmission} Last_chunk:{last_chunk}")
    print(f"Data:{data.to_json()}")
    return packet


def get_bits(control_bits_bytes):
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


def unpack_data(packet):
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
    print(f"Details: control_bits:{get_bits(control_bits)},seq:{seq_num},chunk:{chunk_num}")
    print(f"data_size:{len(data)} retransmission:{retransmission_flag} last_chunk:{last_chunk_flag}")
    print(f"data:{message_object}")
    print("---------------------------------------")
    return control_bits, data_size, seq_num, total, chunk_num, retransmission_flag, last_chunk_flag, message_object


def handle_buffer():
    global buffer_size, received_counter
    if received_counter == 0 and buffer_size > 250:
        buffer_size = int(buffer_size / 2)
    if buffer_size != 1024 and received_counter > 1:
        buffer_size = int(buffer_size * 2)


def slice_data(data):
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
    data = "".join(chunks)
    return data


def reset_timeout(server_socket):
    global time_out
    if received_counter > 1:
        time_out = 3
        server_socket.settimeout(time_out)


if __name__ == '__main__':
    setup_db()
    first_setup()
    print("----------TCP Server----------")
    udp_server_start()
