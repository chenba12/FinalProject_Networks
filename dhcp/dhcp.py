from time import sleep

from scapy.all import *
from scapy.layers.dhcp import DHCP, BOOTP
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether
import random

DHCP_OPTION_DNS_SERVER = 6
server_ip = "192.168.1.1"
dns_server_ip = "192.168.1.2"
app_server_ip = "192.168.1.3"
clients = []
client_ip = "192.168.1.100"
filter_port = "udp and (port 67 or 68)"
network_interface = "enp0s3"
message_types = ["offer", "ack"]
dns_name = "myDNS.com"
subnet_mask = "255.255.255.0"


def generate_client_ip():
    random_end_point = random.randint(100, 256)
    print(random_end_point)
    ip = f"192.168.1.{random_end_point}"
    while ip in clients:
        random_end_point = random.randint(100, 256)
        print(random_end_point)
        ip = f"192.168.1.{random_end_point}"
    clients.append(ip)
    return ip


def handle_dhcp(pkt):
    global client_ip
    sleep(1)
    client_mac = pkt[Ether].src
    xid = pkt[BOOTP].xid
    server_mac = get_if_hwaddr(network_interface)
    if DHCP in pkt and pkt[DHCP].options[0][1] == 1:
        print("----------NEW REQUEST----------")
        print("Received DHCP Discover from " + pkt[Ether].src)
        client_ip = generate_client_ip()
        dhcp_offer = Ether(src=server_mac, dst=client_mac) / \
                     IP(src=server_ip, dst='255.255.255.255') / \
                     UDP(sport=67, dport=68) / \
                     BOOTP(op=2, yiaddr=client_ip, siaddr=server_ip, xid=xid, chaddr=client_mac) / \
                     DHCP(options=[('message-type', message_types[0]),
                                   ('subnet_mask', subnet_mask),
                                   ('router', server_ip),
                                   ('domain', dns_name),
                                   ('name_server', dns_server_ip),
                                   ('end')])
        sendp(dhcp_offer)
        print("Sent DHCP Offer to " + pkt[Ether].src)

    elif DHCP in pkt and pkt[DHCP].options[0][1] == 3:
        print("Received DHCP Request from " + pkt[Ether].src)
        dhcp_ack = Ether(dst=pkt[Ether].src) / IP(src=server_ip, dst="255.255.255.255") / UDP(sport=67,
                                                                                              dport=68) / BOOTP(
            op=2, yiaddr=client_ip, siaddr=server_ip, xid=xid, chaddr=client_mac) / DHCP(
            options=[("message-type", message_types[1]), ("subnet_mask", subnet_mask), ("router", server_ip),
                     ('domain', dns_name),
                     ('name_server', dns_server_ip), "end"])
        sendp(dhcp_ack)
        print("Sent DHCP Ack to " + pkt[Ether].src)
        print("----------DONE----------")


if __name__ == '__main__':
    sniff(filter=filter_port, prn=handle_dhcp, iface=network_interface)
