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
FIN_ACK = 0b11


def setup():
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set the initial sequence number
    server_address = ('localhost', 8000)
    seq_number = random.randint(0, 500)
    client_socket.settimeout(2)
    packet = pack_data(SYN, "SYN", seq_number)
    client_socket.sendto(packet, server_address)
    print(f"Sent SYN message seq_number {seq_number}")
    last_ack = 0
    while True:
        try:
            # Send the SYN message to the server
            packet, address = client_socket.recvfrom(1024)
            control_bits, data, data_size, seq_num = unpack_data(packet)
        except socket.timeout:
            print("Timeout Didn't receive SYN-ACK")
            packet = pack_data(SYN, "SYN", seq_number)
            client_socket.sendto(packet, server_address)
            print(f"Sent SYN message seq_number {seq_number}")
            continue
        if control_bits == SYN_ACK:
            print(f"Received SYN-ACK with seq_num={seq_num} and data={data} from {address}")
            for i in range(10):
                time.sleep(1)
                seq_num += 1
                print(f"sending packet {i} with seq={seq_num}")
                packet = pack_data(DATA_PACKET, f"data +{i}", seq_num)
                client_socket.sendto(packet, server_address)
                try:
                    print(f"Waiting for ACK on packet {i} with seq={seq_num}...")
                    packet, address = client_socket.recvfrom(1024)
                    control_bits, data, data_size, seq_num = unpack_data(packet)
                    if control_bits == ACK:
                        print(f"ACK Received for packet {i} with seq={seq_num}")
                        last_ack = seq_num
                        continue
                except socket.timeout:
                    print(f"Didn't receive ACK for packet {i} with seq={seq_num}")
                    print("Resending...")
                    packet = pack_data(DATA_PACKET, f"data +{i}", last_ack + 1)
                    client_socket.sendto(packet, server_address)

            while True:
                print("----Sent all 10 packets ----")
                print("closing...")
                seq_num += 1
                packet = pack_data(FIN, f"FIN", seq_num)
                client_socket.sendto(packet, server_address)
                try:
                    packet, address = client_socket.recvfrom(1024)
                    control_bits, data, data_size, seq_num = unpack_data(packet)
                    if control_bits == FIN_ACK:
                        print("Got FIN_ACK closing...")
                        client_socket.close()
                        sys.exit(1)
                except socket.timeout:
                    print("Didnt receive FIN-ACK resending...")
                    packet = pack_data(FIN, f"FIN", seq_num)
                    client_socket.sendto(packet, server_address)


if __name__ == '__main__':
    setup()
