from time import sleep
from scapy.all import *
from scapy.layers.dhcp import DHCP, BOOTP
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether
import random

# This is the DHCP server the client will connect to the DHCP server and get an IP randomly generated 192.168.1.XXX
# THe client will also get the IP of the DNS server

# constants
network_interface = "enp0s3"
server_ip = "192.168.1.1"
dns_server_ip = "192.168.1.2"
app_server_ip = "192.168.1.3"
clients = []
client_ip = "192.168.1.100"
filter_port = "udp and (port 67 or 68)"
message_types = ["offer", "ack"]
dns_name = "myDNS.com"
subnet_mask = "255.255.255.0"
client_mac = ""


# Randomly generate an IP for the client 192.168.1.XXX where 100<=XXX<=255
def generate_client_ip():
    random_end_point = random.randint(100, 255)
    print(random_end_point)
    ip = f"192.168.1.{random_end_point}"
    while ip in clients:
        random_end_point = random.randint(100, 255)
        print(random_end_point)
        ip = f"192.168.1.{random_end_point}"
    clients.append(ip)
    return ip


# The DHCP handle method
def handle_dhcp(pkt):
    global client_mac
    sleep(1)
    client_mac = pkt[Ether].src
    xid = pkt[BOOTP].xid
    server_mac = get_if_hwaddr(network_interface)
    # Handle DHCP discovers from the client
    if DHCP in pkt and pkt[DHCP].options[0][1] == 1:
        send_dhcp_offer(client_mac, server_mac, xid)
    # Handle DHCP requests from the client
    elif DHCP in pkt and pkt[DHCP].options[0][1] == 3:
        send_dhcp_ack(client_ip, client_mac, pkt, xid)


# handle sending DHCP ACK after a DHCP request is received from the client
def send_dhcp_ack(c_ip, c_mac, pkt, xid) -> None:
    print(f"----------Received DHCP Request from {c_mac}----------")
    dhcp_ack = Ether(dst=pkt[Ether].src) / IP(src=server_ip, dst="255.255.255.255") / UDP(sport=67,
                                                                                          dport=68) / BOOTP(
        op=2, yiaddr=c_ip, siaddr=server_ip, xid=xid, chaddr=c_mac) / DHCP(
        options=[("message-type", message_types[1]), ("subnet_mask", subnet_mask), ("router", server_ip),
                 ('domain', dns_name),
                 ('name_server', dns_server_ip), "end"])
    sendp(dhcp_ack)
    print(f"Sent DHCP ACK to {c_mac}")
    print("----------DONE----------")


# handle sending DHCP Offer after a DHCP discover is received from the client
def send_dhcp_offer(c_mac, server_mac, xid) -> None:
    global client_ip
    print("----------NEW REQUEST----------")
    print(f"Received DHCP Discover from {c_mac}")
    client_ip = generate_client_ip()
    dhcp_offer = Ether(src=server_mac, dst=c_mac) / \
                 IP(src=server_ip, dst='255.255.255.255') / \
                 UDP(sport=67, dport=68) / \
                 BOOTP(op=2, yiaddr=client_ip, siaddr=server_ip, xid=xid, chaddr=c_mac) / \
                 DHCP(options=[('message-type', message_types[0]),
                               ('subnet_mask', subnet_mask),
                               ('router', server_ip),
                               ('domain', dns_name),
                               ('name_server', dns_server_ip),
                               'end'])
    sendp(dhcp_offer)
    print(f"----------Sent DHCP Offer to {c_mac}----------")


if __name__ == '__main__':
    sniff(filter=filter_port, prn=handle_dhcp, iface=network_interface)
