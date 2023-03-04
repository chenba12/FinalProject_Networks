import random
import socket

control_bits_size = 1
seq_num_size = 4
data_length_size = 4
BUFFER_SIZE = 1024
SYN = 0b10
SYN_ACK = 0b101
ACK = 0b01
DATA_PACKET = 0b00
FIN = 0b1
FIN_ACK = 0b11


def setup():
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket to a public host and a well-known port
    server_socket.bind(('localhost', 8000))
    while True:
        # Receive packet
        packet, address = server_socket.recvfrom(BUFFER_SIZE)
        control_bits, data, data_size, seq_num = unpack_data(packet)
        if control_bits == SYN:
            # process SYN message
            print(f"Received SYN message,sequence number:{seq_num},data size:{data_size},data:{data}")
            # send SYN-ACK message here
            server_socket.settimeout(3)
            seq_num += 1
            packet = pack_data(SYN_ACK, "SYN-ACK", seq_num)
            server_socket.sendto(packet, address)
            print(f"Sent SYN-ACK with seq_num={seq_num}")
        while True:
            packet, address = server_socket.recvfrom(BUFFER_SIZE)
            control_bits, data, data_size, seq_num = unpack_data(packet)
            print(f"Received packet with seq_num={seq_num} and data={data} from {address}")
            if control_bits == DATA_PACKET:
                if random.random() < 0.5:
                    print("dropping...")
                    continue
                packet = pack_data(ACK, "ACK", seq_num)
                server_socket.sendto(packet, address)
                print(f"Sent ACK on packet with seq_num={seq_num}")
            elif control_bits == FIN:
                packet = pack_data(FIN_ACK, "FIN_ACK", seq_num)
                server_socket.sendto(packet, address)
                print(f"Sent FIN_ACK on packet with seq_num={seq_num}")


def pack_data(control_bits, data, seq_num):
    control_bits = control_bits
    data_size = len(data).to_bytes(4, byteorder='big')
    seq_num_bytes = seq_num.to_bytes(4, byteorder='big')
    header = control_bits.to_bytes(1, byteorder='big') + seq_num_bytes + data_size
    packet = header + data.encode('utf-8')
    return packet


def unpack_data(packet):
    control_bits = int.from_bytes(packet[:1], byteorder='big')
    seq_num = int.from_bytes(packet[1:5], byteorder='big')
    data_size = int.from_bytes(packet[5:9], byteorder='big')
    data = packet[9:].decode('utf-8')
    return control_bits, data, data_size, seq_num


if __name__ == '__main__':
    setup()
