import math
import socket
import hashlib
import threading
import time

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
timeout = 3


# header
# | control bits (1 byte) | data size (4 bytes) | seq_number (4 bytes) | chunk_num (4 bytes)
# | retransmission flag (1 byte) | last chunk flag (1 byte) | | checksum (4 bytes) |
def setup():
    global buffer_size
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 8000))
    print("Waiting for Clients")
    while True:
        # Receive packet
        try:
            received_packet, client_address = server_socket.recvfrom(buffer_size)
        except socket.timeout:
            # TODO handle timeout
            pass
            # received_packet, client_address = server_socket.recvfrom(BUFFER_SIZE)
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
            client_list.append(client_address)
            client_thread = threading.Thread(
                target=lambda: handle(client_address, control_bits, data_size, seq_num, chunk_num, retransmission,
                                      last_chunk, data, server_socket))
            client_thread.start()


# header
# | control bits (1 byte) | data size (4 bytes) | seq_number (4 bytes) | chunk_num (4 bytes)
# | retransmission flag (1 byte) | last chunk flag (1 byte) | | checksum (4 bytes) |
def handle(client_address, control_bits, data_size, seq_num, chunk_num, retransmission, last_chunk, data,
           server_socket):
    client_flag = True
    if control_bits == SYN:
        server_socket.settimeout(timeout)
        seq_num += 1
        sent_packet = pack_data(SYN_ACK, seq_num, 0, 0, 0, "SYN-ACK")
        server_socket.sendto(sent_packet, client_address)
    elif control_bits == NAK:

        sent_packet = pack_data(SYN_ACK, seq_num, 0, 0, 0, "SYN-ACK")
        server_socket.sendto(sent_packet, client_address)
    while client_flag:
        try:
            received_packet, client_address = server_socket.recvfrom(buffer_size)
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
        if control_bits == PSH:
            # TODO uncomment to drop packets

            # if random.random() < 0.5:
            #     print("dropping...")
            #     continue
            chunks = slice_data(fake)
            size = len(chunks)
            i = 1
            for chunk in chunks:
                if size - i == 0:
                    last_chunk = 1
                else:
                    last_chunk = 0
                time.sleep(1)

                sent_packet = pack_data(control_bits=PSH_ACK, seq_num=seq_num, chunk_num=size - i, retransmission=0,
                                        last_chunk=last_chunk,
                                        data=chunk)
                server_socket.sendto(sent_packet, client_address)
                waiting_for_ack = True
                while waiting_for_ack:
                    try:
                        received_packet, client_address = server_socket.recvfrom(buffer_size)
                    except socket.timeout:
                        sent_packet = pack_data(control_bits=PSH_ACK, seq_num=seq_num, chunk_num=size, retransmission=0,
                                                last_chunk=last_chunk,
                                                data=chunk)
                        server_socket.sendto(sent_packet, client_address)
                        pass
                    try:
                        control_bits, data, data_size, seq_num, chunk_num, retransmission, last_chunk = unpack_data(
                            received_packet)
                        if control_bits == ACK:
                            print("GOT ACK can send more chunks")
                            waiting_for_ack = False
                    except ValueError:
                        sent_packet = pack_data(NAK, seq_num, 0, 0, 0, "NAK")
                        server_socket.sendto(sent_packet, client_address)
                i += 1
        elif control_bits == FIN:
            while client_flag:
                sent_packet = pack_data(control_bits=FIN_ACK, seq_num=seq_num, chunk_num=0, retransmission=0,
                                        last_chunk=0,
                                        data="FIN_ACK")
                server_socket.sendto(sent_packet, client_address)
                try:
                    received_packet, client_address = server_socket.recvfrom(buffer_size)
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
    # TODO uncomment to make faulty check_sum
    # if random.random() < 0.1:
    #     # introduce random error in checksum
    #     i = random.randint(0, 3)
    #     checksum = checksum[:i] + bytes([checksum[i] ^ 0xFF]) + checksum[i + 1:]
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


fake = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.!!!!!!!!!!!"


def get_buffer_size():
    return buffer_size


def set_buffer_size(value):
    global buffer_size
    buffer_size += value


def slice_data(data):
    # header size
    header_size = 19

    # Calculate the number of chunks
    num_chunks = math.ceil(len(data) / (buffer_size - header_size))
    # Slice the data into chunks
    chunks = []
    for i in range(num_chunks):
        chunk_start = i * (buffer_size - header_size)
        chunk_end = (i + 1) * (buffer_size - header_size)
        chunk = data[chunk_start:chunk_end]
        chunks.append(chunk)
    return chunks


def concatenate_chunks(chunks):
    data = "".join(chunks)
    return data


if __name__ == '__main__':
    setup()
