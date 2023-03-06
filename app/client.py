import json
from scapy.all import *
from scapy.layers.dhcp import DHCP, BOOTP
from scapy.layers.dns import DNSQR, DNS, DNSRR
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether

from games import json_to_game, validate_platform, validate_category, validate_score, validate_year
from message import add_game_message, json_to_message, get_all_message, get_game_by_id_message, \
    get_game_by_name_message, get_game_by_platform_message, get_game_by_category_message, delete_game_message, \
    get_game_by_score_message, get_game_by_year_message, get_game_by_price_message, get_game_by_price_between_message, \
    update_game_message

network_interface = "enp0s3"
client_mac = bytes.fromhex(" ".join(["08", "00", "27", "11", "11", "11"]))
client_ip = "0.0.0.0"
dns_server_ip = ""
filter_port = "udp and (port 67 or 68)"
message_types = ["discover", "request"]
app_server_name = "mySQLApp.com"
app_server_ip = ""
app_Server_port = 30962
app_client_port = 20961
BUFFER_SIZE = 8000


def handle_ip(pkt):
    global dns_server_ip, client_ip
    time.sleep(1)
    if DHCP in pkt and pkt[DHCP].options[0][1] == 2:
        print("---------Offer Received---------")
        print(f"from {pkt[Ether].src}")
        ip = pkt[BOOTP].yiaddr
        mac = pkt[Ether].src
        dhcp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / IP(src=client_ip, dst="255.255.255.255") / UDP(sport=68,
                                                                                                       dport=67) / BOOTP(
            op=1, chaddr=mac) / DHCP(
            options=[("message-type", message_types[1]), ("requested_addr", ip), ("server_id", pkt[IP].src), "end"])
        sendp(dhcp_request)
        print(f"Sent DHCP Request to {pkt[IP].src}")
    if DHCP in pkt and pkt[DHCP].options[0][1] == 5:
        print("----------ACK Received----------")
        if pkt.haslayer(DHCP):
            for option in pkt[DHCP].options:
                if option[0] == "name_server":
                    dns_server_ip = option[1]
        client_ip = pkt[BOOTP].yiaddr
        print(f"Client ip:{client_ip} DNS server ip:{dns_server_ip}")
        return True


def send_dhcp_discover():
    print("----------DHCP Discover----------")
    print(f"Client details: client mac:{client_mac}")
    dhcp_discover = Ether(src=client_mac, dst="ff:ff:ff:ff:ff:ff") / \
                    IP(src=client_ip, dst="255.255.255.255") / \
                    UDP(sport=68, dport=67) / \
                    BOOTP(op=1, chaddr=client_mac) / \
                    DHCP(options=[("message-type", message_types[0]),
                                  ("client_id", client_mac),
                                  ("requested_addr", client_ip),
                                  ("option_list", [6, 3]),
                                  "end"])
    sendp(dhcp_discover, iface=network_interface)
    print("----------Discover Sent----------")


def dns_packet_handle():
    print("----------DNS Request----------")
    print(f"App needed:{app_server_name}")
    dns_query = DNSQR(qname=app_server_name)
    dns_packet = IP(src=client_ip, dst=dns_server_ip) / UDP(sport=12345, dport=53) / DNS(rd=1, qd=dns_query)
    send(dns_packet)


def dns_response(pkt):
    global app_server_ip
    if pkt.haslayer(DNS) and pkt.haslayer(DNSRR):
        print("----------DNS ----------")
        app_address = pkt[DNSRR].rrname.decode().rstrip(".")
        if app_address == app_server_name:
            app_server_ip = pkt[DNSRR].rdata
            print(f"IP of {app_server_name}:{app_server_ip}")
            return True


def connect_to_app_server():
    print("----------TCP Connection----------")
    print(f"Server details: ({app_server_ip} {app_Server_port})")
    client_socket = socket.socket()
    client_socket.connect(("10.0.2.15", app_Server_port))
    print("This is a SQL server")
    handle_request(client_socket)

    client_socket.close()  # close the connection


def handle_request(client_socket):
    running = True
    while running:
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
                    request = get_all_message()
                    client_socket.send(bytes(json.dumps(request.to_json()), encoding="utf-8"))  # send message
                    data = client_socket.recv(BUFFER_SIZE)
                    json_data = json.loads(data.decode("utf-8"))
                    message_object = json_to_message(json_data)
                    for item in message_object.body:
                        game = json_to_game(item)
                        print(game)
                case 2:
                    print("----------SQL Add Game----------")
                    name = input("Please enter Game Title: ")
                    platforms = validate_platform_check()
                    category = validate_category_check()
                    price = validate_price_check()
                    score = validate_score_check()
                    release_year = validate_year_check()
                    request = add_game_message(name=name, platform=platforms, category=category, price=price,
                                               score=score,
                                               release_year=release_year)
                    handle_respond(client_socket, request)
                case 3:
                    print("----------SQL Get Game By ID----------")
                    game_id = validate_id_check()
                    request = get_game_by_id_message(int(game_id))
                    handle_respond(client_socket, request)
                case 4:
                    print("----------SQL Get Game By Name----------")
                    game_name = input("Please enter Game Title: ")
                    request = get_game_by_name_message(game_name)
                    handle_respond(client_socket, request)
                case 5:
                    print("----------SQL Get Games By Platform----------")
                    platforms = validate_platform_check()
                    request = get_game_by_platform_message(platforms)
                    handle_respond(client_socket, request)
                case 6:
                    print("----------SQL Get Games By Category----------")
                    category = validate_category_check()
                    request = get_game_by_category_message(category)
                    handle_respond(client_socket, request)
                case 7:
                    print("----------SQL Delete Game----------")
                    game_id = validate_id_check()
                    request = delete_game_message(game_id)
                    handle_respond(client_socket, request)
                case 8:
                    print("----------SQL Get Games By Score----------")
                    score = validate_score_check()
                    request = get_game_by_score_message(score)
                    handle_respond(client_socket, request)
                case 9:
                    print("----------SQL Get Games By Year----------")
                    year = validate_year_check()
                    request = get_game_by_year_message(year)
                    handle_respond(client_socket, request)
                case 10:
                    print("----------SQL Get Games By Price----------")
                    price = validate_price_check()
                    request = get_game_by_price_message(price)
                    handle_respond(client_socket, request)
                    pass
                case 11:
                    print("----------SQL Get Games By Price range----------")
                    start = validate_price_check("start")
                    end = validate_price_check("end")
                    request = get_game_by_price_between_message(start, end)
                    handle_respond(client_socket, request)
                case 12:
                    print("----------SQL Update Game----------")
                    game_id = validate_id_check()
                    name = input("Please enter Game Title: ")
                    platforms = validate_platform_check()
                    category = validate_category_check()
                    price = validate_price_check()
                    score = validate_score_check()
                    release_year = validate_year_check()
                    request = update_game_message(game_id, name, platforms, category, price, score, release_year)
                    handle_respond(client_socket, request)
                case 13:
                    print("Exit...")
                    break


def validate_price_check(message: str = "") -> float:
    while True:
        try:
            price = float(input(f"Please enter {message} price: "))
            break
        except ValueError:
            print("Invalid input.")
    return price


def validate_id_check() -> int:
    while True:
        try:
            game_id = int(input("Please enter Game id: "))
            break
        except ValueError:
            print("Invalid input.")
    return game_id


def validate_year_check() -> int:
    release_year = 1970
    while True:
        try:
            release_year = int(input("Please enter valid year 1970<=year<=2030: "))
        except ValueError:
            print("Invalid input.")
            continue
        if not validate_year(release_year):
            release_year = int(input("Please enter valid year 1970<=year<=2030: "))
        else:
            break
    return release_year


def validate_score_check() -> float:
    score = 0
    while True:
        try:
            score = float(input("Please valid score 0<=score<=100: "))
        except ValueError:
            print("Invalid input.")
            continue
        if not validate_score(score):
            score = float(input("Please valid score 0<=score<=100: "))
        else:
            break
    return score


def validate_category_check() -> str:
    category = input(
        "JRPG, Adventure, Shooter, Action, Fighting, Platformer, RPG, Survival, Sport, MMO: ")
    while True:
        if not validate_category(category):
            print("Please enter a valid category")
            category = input(
                "JRPG, Adventure, Shooter, Action, Fighting, Platformer, RPG, Survival, Sport, MMO: ")
        else:
            break
    return category


def validate_platform_check() -> str:
    print("Please enter a platform:")
    platforms = input("Switch, PC, Playstation5, Playstation4, Xbox series S: ")
    while True:
        if not validate_platform(platforms):
            print("Please enter a valid platform")
            platforms = input("Switch, PC, Playstation5, Playstation4, Xbox series S: ")
        else:
            break
    return platforms


def handle_respond(client_socket, request):
    client_socket.send(bytes(json.dumps(request.to_json()), encoding="utf-8"))  # send message
    data = client_socket.recv(BUFFER_SIZE)
    json_data = json.loads(data.decode("utf-8"))
    message_object = json_to_message(json_data)
    if len(message_object.body) == 0:
        print("No Game found")
    elif message_object.func == "error":
        print("No Game found")
    else:
        for item in message_object.body:
            game = json_to_game(item)
            print(game)


if __name__ == '__main__':
    # send_dhcp_discover()
    # sniff(filter=filter_port, timeout=10, count=3, prn=handle_ip, iface=network_interface)
    # print("IP address assigned to client: " + client_ip)
    # print("DNS server IP: " + dns_server_ip)
    # print("----------DHCP DONE----------")
    # dns_packet_handle()
    # sniff(filter=f"udp port 53 and src {dns_server_ip}", prn=dns_response, timeout=10, count=1)
    # print("----------DNS DONE----------")

    connect_to_app_server()
