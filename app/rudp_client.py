import socket
import sys
import time
import random
from rudp_server import pack_data, unpack_data, concatenate_chunks, SYN, SYN_ACK, PSH_ACK, PSH, FIN, FIN_ACK, ACK, NAK

BUFFER_SIZE = 1024
data_chunks = []


def setup():
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set the initial sequence number
    server_address = ('localhost', 8000)
    seq_num = random.randint(0, 500)
    client_socket.settimeout(2)
    sent_packet = pack_data(SYN, seq_num, 0, 0, 0, "SYN")
    client_socket.sendto(sent_packet, server_address)
    while True:
        try:
            # Send the SYN message to the server
            received_packet, address = client_socket.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            print("Timeout Didn't receive SYN-ACK")
            sent_packet = pack_data(SYN, seq_num, 0, 0, 0, "SYN")
            client_socket.sendto(sent_packet, server_address)
            continue
        try:
            control_bits, data, data_size, seq_num, chunk_num, retransmission, last_chunk = unpack_data(
                received_packet)
        except ValueError:
            print(f"Got bad check_sum seq_num={seq_num}")
            sent_packet = pack_data(NAK, seq_num, 0, 0, 0, "NAK")
            client_socket.sendto(sent_packet, server_address)
            continue
        if control_bits == SYN_ACK:
            last_ack = seq_num
            for i in range(1):
                seq_num += 1
                print(f"PUSHED {i}")
                sent_packet = pack_data(PSH, seq_num, 0, 0, 0, f"data {i}")
                client_socket.sendto(sent_packet, server_address)
                while True:
                    try:
                        print(f"Waiting for ACK on packet {i} with seq={last_ack + 1}...")
                        received_packet, address = client_socket.recvfrom(BUFFER_SIZE)
                        try:
                            control_bits, data, data_size, seq_num, chunk_num, retransmission, last_chunk = unpack_data(
                                received_packet)
                        except ValueError:
                            print(f"Got bad check_sum seq_num={seq_num}")
                            sent_packet = pack_data(NAK, seq_num, 0, 0, 0, "NAK")
                            client_socket.sendto(sent_packet, server_address)
                            continue
                        if control_bits == PSH_ACK:
                            last_ack = seq_num
                            data_chunks.append(data)
                            sent_packet = pack_data(ACK, seq_num, 0, 0, 0, "")
                            client_socket.sendto(sent_packet, server_address)
                            print(f"THE CHUNK IS {chunk_num} last? {last_chunk}")
                            if last_chunk == 1 and len(data_chunks) == chunk_num:
                                print("GOT THE FULL DATA")
                                full_data = concatenate_chunks(data_chunks)
                                print(full_data)
                                break

                    except socket.timeout:
                        # TODO handle timeout
                        print("why timeout?")
                        # print(f"Didn't receive ACK for packet {i} with seq={seq_num}")
                        # sent_packet = pack_data(PSH, last_ack + 1, 0, 0, 0, f"data {i}")
                        # client_socket.sendto(sent_packet, server_address)

            while True:
                print("----Sent all 5 packets ----")
                print("closing...")
                seq_num += 1
                sent_packet = pack_data(FIN, seq_num, 0, 0, 0, f"FIN")
                client_socket.sendto(sent_packet, server_address)
                try:
                    received_packet, address = client_socket.recvfrom(BUFFER_SIZE)
                except socket.timeout:
                    print("Didnt receive FIN-ACK resending...")
                    sent_packet = pack_data(FIN, seq_num, 0, 0, 0, f"FIN")
                    client_socket.sendto(sent_packet, server_address)
                try:
                    control_bits, data, data_size, seq_num, chunk_num, retransmission, last_chunk = unpack_data(
                        received_packet)
                except ValueError:
                    print(f"Got bad check_sum seq_num={seq_num}")
                    sent_packet = pack_data(NAK, seq_num, 0, 0, 0, "NAK")
                    client_socket.sendto(sent_packet, server_address)
                    continue
                if control_bits == FIN_ACK:
                    print("Got FIN_ACK closing...")
                    sent_packet = pack_data(FIN_ACK, seq_num, 0, 0, 0, f"FIN_ACK")
                    client_socket.sendto(sent_packet, server_address)
                    client_socket.close()
                    sys.exit(1)
        elif control_bits == NAK:
            print(f"Got bad check_sum seq_num={seq_num}")
            client_socket.sendto(sent_packet, server_address)


if __name__ == '__main__':
    setup()
