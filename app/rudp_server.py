import random
import socket
import sys
import hashlib

control_bits_size = 1
seq_num_size = 4
data_length_size = 4
BUFFER_SIZE = 1024
SYN = 0b10
SYN_ACK = 0b101
ACK = 0b01
DATA_PACKET = 0b00
FIN = 0b1
FIN_ACK = 0b1001
NAK = 0b11


def setup():
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind the socket to a public host and a well-known port
    server_socket.bind(('localhost', 8000))
    client_flag = True
    while True:
        # Receive packet
        print("Waiting for Clients")
        received_packet, client_address = server_socket.recvfrom(BUFFER_SIZE)
        client_flag = True
        print("New Client connected {ad}")
        try:
            control_bits, data, data_size, seq_num = unpack_data(received_packet)
        except ValueError:
            print("Sending NAK")
            seq_num = int.from_bytes(received_packet[1:5], byteorder='big')
            received_packet = pack_data(NAK, "", seq_num)
            server_socket.sendto(received_packet, client_address)
            continue
        if control_bits == SYN:
            # process SYN message
            print(f"Received SYN message,sequence number:{seq_num},data size:{data_size},data:{data}")
            # send SYN-ACK message here
            server_socket.settimeout(3)
            seq_num += 1
            sent_packet = pack_data(SYN_ACK, "SYN-ACK", seq_num)
            server_socket.sendto(sent_packet, client_address)
            print(f"Sent SYN-ACK with seq_num={seq_num}")
        elif control_bits == NAK:
            print("Got NAK resending last message")
            sent_packet = pack_data(SYN_ACK, "SYN-ACK", seq_num)
            server_socket.sendto(sent_packet, client_address)
        while client_flag:
            try:
                received_packet, client_address = server_socket.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                print(f"Timeout: {seq_num}")
                sent_packet = pack_data(SYN_ACK, "SYN-ACK", seq_num)
                server_socket.sendto(sent_packet, client_address)
                continue
            try:
                control_bits, data, data_size, seq_num = unpack_data(received_packet)
            except ValueError:
                print(f"Got bad check_sum seq_num={seq_num}")
                sent_packet = pack_data(NAK, "NAK", seq_num)
                server_socket.sendto(sent_packet, client_address)
            print(f"Received packet with seq_num={seq_num} and data={data} from {client_address}")
            if control_bits == DATA_PACKET:
                if random.random() < 0.5:
                    print("dropping...")
                    continue
                sent_packet = pack_data(ACK, "ACK", seq_num)
                server_socket.sendto(sent_packet, client_address)
                print(f"Sent ACK on packet with seq_num={seq_num}")
            elif control_bits == FIN:
                while client_flag:
                    sent_packet = pack_data(FIN_ACK, "FIN_ACK", seq_num)
                    server_socket.sendto(sent_packet, client_address)
                    print(f"Sent FIN_ACK on packet with seq_num={seq_num}")
                    try:
                        received_packet, client_address = server_socket.recvfrom(BUFFER_SIZE)
                    except socket.timeout:
                        print(f"Timeout: seq_num={seq_num}")
                        sent_packet = pack_data(FIN_ACK, "FIN_ACK", seq_num)
                        server_socket.sendto(sent_packet, client_address)
                        print(f"Sent FIN_ACK on packet with seq_num={seq_num}")
                        continue
                    try:
                        control_bits, data, data_size, seq_num = unpack_data(received_packet)
                    except ValueError:
                        print(f"Got bad check_sum seq_num={seq_num}")
                        sent_packet = pack_data(NAK, "NAK", seq_num)
                        server_socket.sendto(sent_packet, client_address)
                    if control_bits == FIN_ACK:
                        print("Closing...")
                        client_flag = False
                        server_socket.settimeout(None)
                        break
            elif control_bits == NAK:
                print(f"Got NAK resending last message {seq_num}")
                server_socket.sendto(sent_packet, client_address)


def pack_data(control_bits, data, seq_num):
    control_bits = control_bits
    data_size = len(data).to_bytes(4, byteorder='big')
    seq_num_bytes = seq_num.to_bytes(4, byteorder='big')
    header = control_bits.to_bytes(1, byteorder='big') + seq_num_bytes + data_size
    checksum = hashlib.sha256(header + data.encode('utf-8')).digest()[:4]
    if random.random() < 0.1:
        # introduce random error in checksum
        i = random.randint(0, 3)
        checksum = checksum[:i] + bytes([checksum[i] ^ 0xFF]) + checksum[i + 1:]
    packet = header + checksum + data.encode('utf-8')
    return packet


def unpack_data(packet):
    control_bits = int.from_bytes(packet[:1], byteorder='big')
    seq_num = int.from_bytes(packet[1:5], byteorder='big')
    data_size = int.from_bytes(packet[5:9], byteorder='big')
    checksum = packet[9:13]
    data = packet[13:].decode('utf-8')

    # Compute checksum over the received packet (excluding the checksum field)
    header = packet[:9]
    computed_checksum = hashlib.sha256(header + data.encode('utf-8')).digest()[:4]

    # Verify the checksum
    if checksum != computed_checksum:
        raise ValueError('Packet has been corrupted')
    return control_bits, data, data_size, seq_num


if __name__ == '__main__':
    setup()
