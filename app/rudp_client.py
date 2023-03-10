import socket
import sys
import random

from client_sender import validate_platform_check, validate_category_check, validate_price_check, \
    validate_score_check, validate_year_check, validate_id_check, get_app_server_ip, get_app_server_port, \
    validate_price_range_check, validate_name_check
from message import get_all_message, add_game_message, get_game_by_id_message, \
    get_game_by_name_message, get_game_by_platform_message, get_game_by_category_message, delete_game_message, \
    get_game_by_score_message, get_game_by_year_message, get_game_by_price_message, get_game_by_price_between_message, \
    update_game_message, Message
from rudp_server import pack_data, unpack_data, concatenate_chunks, SYN, SYN_ACK, PSH_ACK, PSH, \
    FIN, FIN_ACK, ACK, NAK, handle_buffer, handle_recv_success, handle_timeout_error

# constants
data_chunks = []
buffer_size = 1024
received_counter = 0
time_out = 2
retransmission = 0


def udp_connect_to_server():
    global buffer_size, received_counter, time_out, retransmission
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set the initial sequence number
    server_address = (get_app_server_ip(), get_app_server_port())
    seq_num = random.randint(0, 1000)
    client_socket.settimeout(time_out)
    # Send the SYN message to the server

    while True:
        try:
            sent_packet = pack_data(SYN, seq_num, 0, 0, retransmission, 0, Message("SYN", ""))
            client_socket.sendto(sent_packet, server_address)
            # Receive the SYN-ACK message to the server
            received_packet, address = client_socket.recvfrom(buffer_size)
        except socket.timeout:
            print("Timeout Didn't receive SYN-ACK")
            handle_timeout_error(client_socket)
            continue
        handle_recv_success(client_socket)
        try:
            control_bits, data_size, seq_num, total, chunk_num, \
                retransmission_flag, last_chunk_flag, data = unpack_data(received_packet)
        except ValueError:
            print(f"Got bad check_sum seq_num={seq_num}")
            sent_packet = pack_data(NAK, seq_num, 0, 0, retransmission, 0, Message("NAK", ""))
            client_socket.sendto(sent_packet, server_address)
            continue
        if control_bits == SYN_ACK:
            running = True
            client_socket.settimeout(None)
            while running:
                print("---------------------------------------")
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
                            seq_num += 1
                            request = get_all_message()
                            sent_packet, seq_num = handle_request(client_socket, seq_num,
                                                                  request, server_address)
                        case 2:
                            print("----------SQL Add Game----------")
                            seq_num += 1
                            game_name = validate_name_check()
                            platforms = validate_platform_check()
                            category = validate_category_check()
                            price = validate_price_check()
                            score = validate_score_check()
                            release_year = validate_year_check()
                            request = add_game_message(name=game_name, platform=platforms, category=category, price=price,
                                                       score=score,
                                                       release_year=release_year)
                            sent_packet, seq_num = handle_request(client_socket, seq_num,
                                                                  request, server_address)
                        case 3:
                            print("----------SQL Get Game By ID----------")
                            seq_num += 1
                            game_id = validate_id_check()
                            request = get_game_by_id_message(int(game_id))
                            sent_packet, seq_num = handle_request(client_socket, seq_num,
                                                                  request, server_address)
                        case 4:
                            print("----------SQL Get Game By Name----------")
                            seq_num += 1
                            game_name = validate_name_check()
                            request = get_game_by_name_message(game_name)
                            sent_packet, seq_num = handle_request(client_socket, seq_num,
                                                                  request, server_address)
                        case 5:
                            print("----------SQL Get Games By Platform----------")
                            seq_num += 1
                            platforms = validate_platform_check()
                            request = get_game_by_platform_message(platforms)
                            sent_packet, seq_num = handle_request(client_socket, seq_num,
                                                                  request, server_address)
                        case 6:
                            print("----------SQL Get Games By Category----------")
                            seq_num += 1
                            category = validate_category_check()
                            request = get_game_by_category_message(category)
                            sent_packet, seq_num = handle_request(client_socket, seq_num,
                                                                  request, server_address)
                        case 7:
                            print("----------SQL Delete Game----------")
                            seq_num += 1
                            game_id = validate_id_check()
                            request = delete_game_message(game_id)
                            sent_packet, seq_num = handle_request(client_socket, seq_num,
                                                                  request, server_address)
                        case 8:
                            print("----------SQL Get Games By Score----------")
                            seq_num += 1
                            score = validate_score_check()
                            request = get_game_by_score_message(score)
                            sent_packet, seq_num = handle_request(client_socket, seq_num,
                                                                  request, server_address)
                        case 9:
                            print("----------SQL Get Games By Year----------")
                            seq_num += 1
                            year = validate_year_check()
                            request = get_game_by_year_message(year)
                            sent_packet, seq_num = handle_request(client_socket, seq_num,
                                                                  request, server_address)
                        case 10:
                            print("----------SQL Get Games By Price----------")
                            seq_num += 1
                            price = validate_price_check()
                            request = get_game_by_price_message(price)
                            sent_packet, seq_num = handle_request(client_socket, seq_num,
                                                                  request, server_address)
                            pass
                        case 11:
                            print("----------SQL Get Games By Price range----------")
                            seq_num += 1
                            start, end = validate_price_range_check()
                            request = get_game_by_price_between_message(start, end)
                            sent_packet, seq_num = handle_request(client_socket, seq_num,
                                                                  request, server_address)
                        case 12:
                            print("----------SQL Update Game----------")
                            seq_num += 1
                            game_id = validate_id_check()
                            game_name = validate_name_check()
                            platforms = validate_platform_check()
                            category = validate_category_check()
                            price = validate_price_check()
                            score = validate_score_check()
                            release_year = validate_year_check()
                            request = update_game_message(game_id, game_name, platforms, category, price, score,
                                                          release_year)
                            sent_packet, seq_num = handle_request(client_socket, seq_num,
                                                                  request, server_address)
                        case 13:
                            print("Exit...")
                            break
            sent_packet, seq_num = end_connection(client_socket, seq_num, server_address)
        elif control_bits == NAK:
            print(f"Got bad check_sum seq_num={seq_num}")
            client_socket.sendto(sent_packet, server_address)


def handle_request(client_socket, seq_num, request, server_address):
    global time_out, received_counter, buffer_size, retransmission
    client_socket.settimeout(time_out)
    sent_packet = pack_data(PSH, seq_num, 0, 0, retransmission, 0, request)
    client_socket.sendto(sent_packet, server_address)
    timed_out = False
    while True:
        try:
            if timed_out:
                sent_packet = pack_data(ACK, seq_num, 0, 0, 1, 0, Message("ACK", ""))
            print(f"Waiting for ACK")
            received_packet, address = client_socket.recvfrom(buffer_size)
            try:
                control_bits, data_size, seq_num, total, chunk_num, \
                    retransmission_flag, last_chunk_flag, data = unpack_data(received_packet)
            except ValueError:
                print(f"Got bad check_sum seq_num={seq_num}")
                sent_packet = pack_data(NAK, seq_num, 0, 0, retransmission, 0, Message("NAK", ""))
                client_socket.sendto(sent_packet, server_address)
                continue
            if control_bits == PSH_ACK:
                data_chunks.append(data.body)
                sent_packet = pack_data(ACK, seq_num, 0, 0, retransmission, 0, Message("ACK", ""))
                client_socket.sendto(sent_packet, server_address)
                if last_chunk_flag == 1 and len(data_chunks) == total:
                    full_data = concatenate_chunks(data_chunks)
                    print(full_data)
                    data_chunks.clear()
                    break
        except socket.timeout:
            print("Timeout")
            timed_out = True
            handle_timeout_error(client_socket)
            continue
        handle_recv_success(client_socket)
    return sent_packet, seq_num


def end_connection(client_socket, seq_num, server_address):
    global time_out, received_counter, time_out, retransmission
    client_socket.settimeout(time_out)
    while True:
        print("----------Closing connection----------")
        seq_num += 1
        sent_packet = pack_data(FIN, seq_num, 0, 0, retransmission, 0, Message("FIN", ""))
        try:
            client_socket.sendto(sent_packet, server_address)
            received_packet, address = client_socket.recvfrom(buffer_size)
        except socket.timeout:
            print("Didnt receive FIN-ACK resending...")
            handle_timeout_error(client_socket)
            continue
        handle_recv_success(client_socket)
        try:
            control_bits, data_size, seq_num, total, chunk_num, \
                retransmission_flag, last_chunk_flag, data = unpack_data(received_packet)
        except ValueError:
            print(f"Got bad check_sum seq_num={seq_num}")
            sent_packet = pack_data(NAK, seq_num, 0, 0, 0, 0, Message("NAK", ""))
            client_socket.sendto(sent_packet, server_address)
            continue
        if control_bits == FIN_ACK:
            print("Got FIN_ACK closing...")
            sent_packet = pack_data(FIN_ACK, seq_num, 0, 0, 0, 0, Message("FIN-ACK", ""))
            client_socket.sendto(sent_packet, server_address)
            client_socket.close()
            sys.exit(1)
    return sent_packet, seq_num


def reset_timeout(client_socket):
    global time_out
    if received_counter > 1:
        time_out = 2
        client_socket.settimeout(time_out)

# for tests
# if __name__ == '__main__':
#     udp_connect_to_server()
