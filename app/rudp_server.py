import socket
import hashlib
import threading

BUFFER_SIZE = 1024
SYN = 0b10
SYN_ACK = 0b101
ACK = 0b01
DATA_PACKET = 0b00
FIN = 0b1
FIN_ACK = 0b1001
NAK = 0b11
client_list = []


def setup():
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind the socket to a public host and a well-known port
    server_socket.bind(('localhost', 8000))
    client_flag = True
    print("Waiting for Clients")
    while True:
        # Receive packet
        try:
            received_packet, client_address = server_socket.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            received_packet, client_address = server_socket.recvfrom(BUFFER_SIZE)
        try:
            control_bits, data, data_size, seq_num, chunk_num, retransmission, last_chunk = unpack_data(
                received_packet)
        except ValueError:
            print("Sending NAK")
            seq_num = int.from_bytes(received_packet[1:5], byteorder='big')
            received_packet = pack_data(NAK, seq_num, 0, 0, 0, "")
            server_socket.sendto(received_packet, client_address)
            continue

        if client_address not in client_list:
            print(f"---------NEW Client: {client_address} seq_number={seq_num}---------")
            client_thread = threading.Thread(
                target=lambda: handle(client_address, control_bits, data_size, seq_num, chunk_num, retransmission,
                                      last_chunk, data, server_socket))
            client_thread.start()
            client_list.append(client_address)


# header
# | control bits (1 byte) | data size (4 bytes) | seq_number (4 bytes) | chunk_num (4 bytes)
# | retransmission flag (1 byte) | last chunk flag (1 byte) | | checksum (4 bytes) |
def handle(client_address, control_bits, data_size, seq_num, chunk_num, retransmission, last_chunk, data,
           server_socket):
    print(f"New Client connected {client_address} ")
    print(f"Details: {data_size} {seq_num} {chunk_num} {retransmission} {last_chunk}")
    client_flag = True
    if control_bits == SYN:
        # process SYN message
        # send SYN-ACK message here
        server_socket.settimeout(3)
        seq_num += 1
        sent_packet = pack_data(SYN_ACK, seq_num, 0, 0, 0, "SYN-ACK")
        server_socket.sendto(sent_packet, client_address)
    elif control_bits == NAK:
        sent_packet = pack_data(SYN_ACK, seq_num, 0, 0, 0, "SYN-ACK")
        server_socket.sendto(sent_packet, client_address)
    while client_flag:
        try:
            received_packet, client_address = server_socket.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            print(f"Timeout: {seq_num}")
            sent_packet = pack_data(SYN_ACK, seq_num, 0, 0, 0, "SYN-ACK")
            server_socket.sendto(sent_packet, client_address)
            continue
        try:
            control_bits, data, data_size, seq_num, chunk_num, retransmission, last_chunk = unpack_data(
                received_packet)
        except ValueError:
            sent_packet = pack_data(NAK, seq_num, 0, 0, 0, "NAK")
            server_socket.sendto(sent_packet, client_address)
        if control_bits == DATA_PACKET:
            # TODO uncomment to drop packets

            # if random.random() < 0.5:
            #     print("dropping...")
            #     continue
            sent_packet = pack_data(ACK, seq_num, 0, 0, 0, "ACK")
            server_socket.sendto(sent_packet, client_address)
        elif control_bits == FIN:
            while client_flag:
                sent_packet = pack_data(FIN_ACK, seq_num, 0, 0, 0, "FIN_ACK")
                server_socket.sendto(sent_packet, client_address)
                try:
                    received_packet, client_address = server_socket.recvfrom(BUFFER_SIZE)
                except socket.timeout:
                    print(f"Timeout: seq_num={seq_num}")
                    sent_packet = pack_data(FIN_ACK, seq_num, 0, 0, 0, "FIN_ACK")
                    server_socket.sendto(sent_packet, client_address)
                    continue
                try:
                    control_bits, data, data_size, seq_num, chunk_num, retransmission, last_chunk = unpack_data(
                        received_packet)
                except ValueError:
                    sent_packet = pack_data(NAK, seq_num, 0, 0, 0, "NAK")
                    server_socket.sendto(sent_packet, client_address)
                if control_bits == FIN_ACK:
                    print(f"---------Closing communication with: {client_address}---------")
                    client_flag = False
                    server_socket.settimeout(None)
                    client_list.remove(client_address)
                    break
        elif control_bits == NAK:
            server_socket.sendto(sent_packet, client_address)


# header
# | control bits (1 byte) | data size (4 bytes) | seq_number (4 bytes) | chunk_num (4 bytes)
# | retransmission flag (1 byte) | last chunk flag (1 byte) | | checksum (4 bytes) |
def pack_data(control_bits, seq_num, chunk_num, retransmission, last_chunk, data):
    control_bits_bytes = control_bits.to_bytes(1, byteorder='big')
    data_size_bytes = len(data).to_bytes(4, byteorder='big')
    seq_num_bytes = seq_num.to_bytes(4, byteorder='big')
    chunk_num_bytes = chunk_num.to_bytes(4, byteorder='big')
    retransmission_flag = retransmission.to_bytes(1, byteorder='big')
    last_chunk_flag = last_chunk.to_bytes(1, byteorder='big')
    header = control_bits_bytes + data_size_bytes + seq_num_bytes + chunk_num_bytes \
             + retransmission_flag + last_chunk_flag
    checksum = hashlib.sha256(header).digest()[:4]
    packet = header + checksum + data.encode('utf-8')
    print("--------------Sent packet--------------")
    print(f"Details: control_bits:{get_bits(control_bits)},seq:{seq_num},chunk:{chunk_num}")
    print(f"data_size:{len(data)} retransmission:{retransmission} last_chunk:{last_chunk}")
    print(f"data:{data}")
    return packet


def get_bits(control_bits_bytes):
    if control_bits_bytes == SYN:
        return "SYN"
    elif control_bits_bytes == SYN_ACK:
        return "SYN_ACK"
    elif control_bits_bytes == DATA_PACKET:
        return "DATA_PACKET"
    elif control_bits_bytes == ACK:
        return "ACK"
    elif control_bits_bytes == FIN:
        return "FIN"
    elif control_bits_bytes == FIN_ACK:
        return "FIN_ACK"
    elif control_bits_bytes == NAK:
        return "NAK"
    else:
        print(control_bits_bytes.to_bytes(1, byteorder='big'))
        print(SYN)
        raise IOError("error")


def unpack_data(packet):
    control_bits = int.from_bytes(packet[:1], byteorder='big')
    data_size = int.from_bytes(packet[1:5], byteorder='big')
    seq_num = int.from_bytes(packet[5:9], byteorder='big')
    chunk_num = int.from_bytes(packet[9:13], byteorder='big')
    retransmission_flag = int.from_bytes(packet[13:14], byteorder='big')
    last_chunk_flag = int.from_bytes(packet[14:15], byteorder='big')
    checksum = packet[15:19]
    data = packet[19:].decode('utf-8')

    # Compute checksum over the received packet (excluding the checksum field)
    header = packet[:15]
    computed_checksum = hashlib.sha256(header).digest()[:4]

    # Verify the checksum
    if checksum != computed_checksum:
        raise ValueError('Packet has been corrupted')
    print("------------Received packet------------")
    print(f"Details: control_bits:{get_bits(control_bits)},seq:{seq_num},chunk:{chunk_num}")
    print(f"data_size:{len(data)} retransmission:{retransmission_flag} last_chunk:{last_chunk_flag}")
    print(f"data:{data}")
    print("---------------------------------------")
    return control_bits, data, data_size, seq_num, chunk_num, retransmission_flag, last_chunk_flag


if __name__ == '__main__':
    setup()
