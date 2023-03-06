import socket
import sys
import random
from rudp_server import pack_data, unpack_data, concatenate_chunks, SYN, SYN_ACK, PSH_ACK, PSH, \
    FIN, FIN_ACK, ACK, NAK, handle_buffer

# constants
data_chunks = []
buffer_size = 1024
received_counter = 0
time_out = 2


def connect_to_server():
    global buffer_size, received_counter, time_out

    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set the initial sequence number
    server_address = ('localhost', 8000)
    seq_num = random.randint(0, 1000)
    client_socket.settimeout(time_out)
    # Send the SYN message to the server
    sent_packet = pack_data(SYN, seq_num, 0, 0, 0, 0, "SYN")
    client_socket.sendto(sent_packet, server_address)
    while True:
        try:
            # Receive the SYN-ACK message to the server
            received_packet, address = client_socket.recvfrom(buffer_size)
        except socket.timeout:
            print("Timeout Didn't receive SYN-ACK")
            time_out += 1
            client_socket.settimeout(time_out)
            received_counter = 0
            handle_buffer()
            sent_packet = pack_data(SYN, seq_num, 0, 0, 0, 0, "SYN")
            client_socket.sendto(sent_packet, server_address)
            continue
        received_counter += 1
        reset_timeout(client_socket)
        try:
            control_bits, data_size, seq_num, total, chunk_num, \
                retransmission_flag, last_chunk_flag, data = unpack_data(received_packet)
        except ValueError:
            print(f"Got bad check_sum seq_num={seq_num}")
            sent_packet = pack_data(NAK, seq_num, 0, 0, 0, 0, "NAK")
            client_socket.sendto(sent_packet, server_address)
            continue
        if control_bits == SYN_ACK:
            for i in range(1):
                print("INSIDE LOOP")
                seq_num += 1
                sent_packet = pack_data(PSH, seq_num, 0, 0, 0, 0, f"data {i}")
                client_socket.sendto(sent_packet, server_address)
                while True:
                    try:
                        print(f"Waiting for ACK")
                        received_packet, address = client_socket.recvfrom(buffer_size)
                        try:
                            control_bits, data_size, seq_num, total, chunk_num, \
                                retransmission_flag, last_chunk_flag, data = unpack_data(received_packet)
                        except ValueError:
                            print(f"Got bad check_sum seq_num={seq_num}")
                            sent_packet = pack_data(NAK, seq_num, 0, 0, 0, 0, "NAK")
                            client_socket.sendto(sent_packet, server_address)
                            continue
                        if control_bits == PSH_ACK:
                            data_chunks.append(data)
                            sent_packet = pack_data(ACK, seq_num, 0, 0, 0, 0, "")
                            client_socket.sendto(sent_packet, server_address)
                            print(f"THE CHUNK IS {chunk_num} last? {last_chunk_flag}")
                            print(len(data_chunks))
                            print(total)
                            if last_chunk_flag == 1 and len(data_chunks) == total:
                                full_data = concatenate_chunks(data_chunks)
                                print(full_data)
                                data_chunks.clear()
                                sent_packet, seq_num = end_connection(client_socket, received_packet,
                                                                      seq_num, server_address)
                                break
                    except socket.timeout:
                        # TODO check
                        print("why timeout?")
                        time_out += 1
                        client_socket.settimeout(time_out)
                        received_counter = 0
                        handle_buffer()
                        # sent_packet = pack_data(PSH, seq_num, 0, 0, 0, f"data")
                        # client_socket.sendto(sent_packet, server_address)
                    received_counter += 1
                    reset_timeout(client_socket)
        elif control_bits == NAK:
            print(f"Got bad check_sum seq_num={seq_num}")
            client_socket.sendto(sent_packet, server_address)


def end_connection(client_socket, received_packet, seq_num, server_address):
    global time_out, received_counter, time_out
    while True:
        print("----Sent all 5 packets ----")
        print("closing...")
        seq_num += 1
        sent_packet = pack_data(FIN, seq_num, 0, 0, 0, 0, f"FIN")
        client_socket.sendto(sent_packet, server_address)
        try:
            received_packet, address = client_socket.recvfrom(buffer_size)
        except socket.timeout:
            print("Didnt receive FIN-ACK resending...")
            time_out += 1
            client_socket.settimeout(time_out)
            received_counter = 0
            handle_buffer()
            sent_packet = pack_data(FIN, seq_num, 0, 0, 0, 0, f"FIN")
            client_socket.sendto(sent_packet, server_address)
        received_counter += 1
        reset_timeout(client_socket)
        try:
            control_bits, data_size, seq_num, total, chunk_num, \
                retransmission_flag, last_chunk_flag, data = unpack_data(received_packet)
        except ValueError:
            print(f"Got bad check_sum seq_num={seq_num}")
            sent_packet = pack_data(NAK, seq_num, 0, 0, 0, 0, "NAK")
            client_socket.sendto(sent_packet, server_address)
            continue
        if control_bits == FIN_ACK:
            print("Got FIN_ACK closing...")
            sent_packet = pack_data(FIN_ACK, seq_num, 0, 0, 0, 0, f"FIN_ACK")
            client_socket.sendto(sent_packet, server_address)
            client_socket.close()
            sys.exit(1)
    return sent_packet, seq_num


def reset_timeout(client_socket):
    global time_out
    if received_counter > 1:
        time_out = 2
        client_socket.settimeout(time_out)


if __name__ == '__main__':
    connect_to_server()
