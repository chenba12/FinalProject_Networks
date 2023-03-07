from scapy.all import *
from scapy.layers.dhcp import DHCP, BOOTP
from scapy.layers.dns import DNSQR, DNS, DNSRR
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether

from games import validate_platform, validate_category, validate_score, validate_year
mac_str = uuid.getnode()
client_mac = ':'.join(['{:02x}'.format((mac_str >> i) & 0xff) for i in range(0, 48, 8)])
network_interface = "enp0s3"
client_ip = "0.0.0.0"
dns_server_ip = ""
filter_port = "udp and (port 67 or 68)"
message_types = ["discover", "request"]
app_server_name = "mySQLApp.com"
app_server_ip = ""
app_server_port = 30962
app_client_port = 20961


def get_client_ip():
    global client_ip
    return client_ip


def get_dns_server_ip():
    global dns_server_ip
    return dns_server_ip


def get_app_server_ip():
    global app_server_ip
    return app_server_ip


def get_app_server_port():
    global app_server_port
    return app_server_port


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
