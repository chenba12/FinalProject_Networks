import socket
import sys
import time
import random
from rudp_server import pack_data, unpack_data

SYN = 0b10
SYN_ACK = 0b101
DATA_PACKET = 0b00
ACK = 0b01
FIN = 0b1
FIN_ACK = 0b1001
NAK = 0b11


def setup():
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set the initial sequence number
    server_address = ('localhost', 8000)
    seq_num = random.randint(0, 500)
    client_socket.settimeout(1)
    last_control = SYN
    sent_packet = pack_data(SYN, "SYN", seq_num)
    client_socket.sendto(sent_packet, server_address)
    print(f"Sent SYN message seq_number {seq_num}")
    while True:
        try:
            # Send the SYN message to the server
            received_packet, address = client_socket.recvfrom(1024)
        except socket.timeout:
            print("Timeout Didn't receive SYN-ACK")
            sent_packet = pack_data(SYN, "SYN", seq_num)
            client_socket.sendto(sent_packet, server_address)
            print(f"Sent SYN message seq_number {seq_num}")
            continue
        try:
            control_bits, data, data_size, seq_num = unpack_data(received_packet)
        except ValueError:
            print(f"Got bad check_sum seq_num={seq_num}")
            sent_packet = pack_data(NAK, "NAK", seq_num)
            client_socket.sendto(sent_packet, server_address)
            continue
        if control_bits == SYN_ACK:
            print(f"Received SYN-ACK with seq_num={seq_num} and data={data} from server")
            last_ack = seq_num
            for i in range(5):
                time.sleep(1)
                seq_num += 1
                print(f"Sending packet {i} with seq={seq_num}")
                sent_packet = pack_data(DATA_PACKET, f"data {i}", seq_num)
                client_socket.sendto(sent_packet, server_address)
                while True:
                    try:
                        print(f"Waiting for ACK on packet {i} with seq={last_ack + 1}...")
                        received_packet, address = client_socket.recvfrom(1024)
                        try:
                            control_bits, data, data_size, seq_num = unpack_data(received_packet)
                        except ValueError:
                            print(f"Got bad check_sum seq_num={seq_num}")
                            sent_packet = pack_data(NAK, "NAK", seq_num)
                            client_socket.sendto(sent_packet, server_address)
                            continue
                        if control_bits == ACK:
                            print(f"ACK Received for packet {i} with seq={seq_num}")
                            if seq_num == last_ack + 1:
                                last_ack = seq_num
                                break
                    except socket.timeout:
                        print(f"Didn't receive ACK for packet {i} with seq={seq_num}")
                        print("Resending...")
                        sent_packet = pack_data(DATA_PACKET, f"data {i}", last_ack + 1)
                        client_socket.sendto(sent_packet, server_address)

            while True:
                print("----Sent all 5 packets ----")
                print("closing...")
                seq_num += 1
                sent_packet = pack_data(FIN, f"FIN", seq_num)
                client_socket.sendto(sent_packet, server_address)
                print(f"Sent FIN message seq_number {seq_num}")
                try:
                    received_packet, address = client_socket.recvfrom(1024)
                except socket.timeout:
                    print("Didnt receive FIN-ACK resending...")
                    sent_packet = pack_data(FIN, f"FIN", seq_num)
                    client_socket.sendto(sent_packet, server_address)
                try:
                    control_bits, data, data_size, seq_num = unpack_data(received_packet)
                except ValueError:
                    print(f"Got bad check_sum seq_num={seq_num}")
                    sent_packet = pack_data(NAK, "NAK", seq_num)
                    client_socket.sendto(sent_packet, server_address)
                    continue
                if control_bits == FIN_ACK:
                    print("Got FIN_ACK closing...")
                    sent_packet = pack_data(FIN_ACK, f"FIN_ACK", seq_num)
                    client_socket.sendto(sent_packet, server_address)
                    client_socket.close()
                    sys.exit(1)
        elif control_bits == NAK:
            print(f"Got bad check_sum seq_num={seq_num}")
            client_socket.sendto(sent_packet, server_address)


if __name__ == '__main__':
    setup()
