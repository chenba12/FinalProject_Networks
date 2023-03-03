import json
from scapy.all import *
from scapy.layers.dhcp import DHCP, BOOTP
from scapy.layers.dns import DNSQR, DNS, DNSRR
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether

from games import json_to_game
from message import add_game_message, json_to_message

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


def handle_ip(pkt):
    global dns_server_ip, client_ip
    time.sleep(1)
    if DHCP in pkt and pkt[DHCP].options[0][1] == 2:
        print("Received DHCP Offer from " + pkt[Ether].src)
        ip = pkt[BOOTP].yiaddr
        mac = pkt[Ether].src
        dhcp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / IP(src=client_ip, dst="255.255.255.255") / UDP(sport=68,
                                                                                                       dport=67) / BOOTP(
            op=1, chaddr=mac) / DHCP(
            options=[("message-type", message_types[1]), ("requested_addr", ip), ("server_id", pkt[IP].src), "end"])
        sendp(dhcp_request)
        print("Sent DHCP Request to " + pkt[IP].src)
    if DHCP in pkt and pkt[DHCP].options[0][1] == 5:
        if pkt.haslayer(DHCP):
            for option in pkt[DHCP].options:
                if option[0] == "name_server":
                    dns_server_ip = option[1]
        client_ip = pkt[BOOTP].yiaddr
        return True


def send_dhcp_discover():
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


def dns_packet_handle():
    dns_query = DNSQR(qname=app_server_name)
    dns_packet = IP(src=client_ip, dst=dns_server_ip) / UDP(sport=12345, dport=53) / DNS(rd=1, qd=dns_query)
    send(dns_packet)


def dns_response(pkt):
    global app_server_ip
    if pkt.haslayer(DNS) and pkt.haslayer(DNSRR):
        app_address = pkt[DNSRR].rrname.decode().rstrip(".")
        if app_address == app_server_name:
            app_server_ip = pkt[DNSRR].rdata
            print(f"DNS response: {app_server_ip}")
            return True


def connect_to_app_server():
    client_socket = socket.socket()  # instantiate
    client_socket.connect(("10.0.2.15", app_Server_port))  # connect to the server
    request = add_game_message("Not a game", "PC", "JRPG", 0, 0.5, 2023)
    client_socket.send(bytes(json.dumps(request.as_dict()), encoding="utf-8"))  # send message
    data = client_socket.recv(1024)  # receive response
    json_data = json.loads(data.decode("utf-8"))  # decode and load as JSON object
    message_object = json_to_message(json_data)
    print(message_object.body)
    game = json_to_game(message_object.body)
    print(game)
    client_socket.close()  # close the connection


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
