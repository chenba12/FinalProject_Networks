from time import sleep

from scapy.all import *
from scapy.layers.dhcp import DHCP, BOOTP
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether

DHCP_OPTION_DNS_SERVER = 6
dns_server_ip = "192.168.1.2"


def handle_dhcp(pkt):
    sleep(1)
    client_mac = pkt[Ether].src
    client_ip = "192.168.1.100"
    xid = pkt[BOOTP].xid
    interface_name = "enp0s3"  # replace with your interface name
    server_mac = get_if_hwaddr(interface_name)
    server_ip = "192.168.1.1"
    subnet_mask = "255.255.255.0"
    if DHCP in pkt and pkt[DHCP].options[0][1] == 1:

        print("Received DHCP Discover from " + pkt[Ether].src)
        # dhcp_offer = Ether(dst=pkt[Ether].src) / IP(src="192.168.1.1", dst="255.255.255.255") / UDP(sport=67,
        #                                                                                             dport=68) / BOOTP(
        #     op=2, yiaddr="192.168.1.100", siaddr="192.168.1.1", xid=pkt[BOOTP].xid) / DHCP(
        #     options=[("message-type", "offer"), ("subnet_mask", "255.255.255.0"), ("router", "192.168.1.1"),
        #              ("name_server", "192.168.1.1"), "end"])
        #
        # sendp(dhcp_offer)
        dhcp_offer = Ether(src=server_mac, dst=client_mac) / \
                     IP(src="192.168.1.1", dst='255.255.255.255') / \
                     UDP(sport=67, dport=68) / \
                     BOOTP(op=2, yiaddr=client_ip, siaddr=server_ip, xid=xid, chaddr=client_mac) / \
                     DHCP(options=[('message-type', 'offer'),
                                   ('subnet_mask', subnet_mask),
                                   ('router', server_ip),
                                   ('domain', 'example.com'),
                                   ('name_server', dns_server_ip),
                                   ('end')])
        sendp(dhcp_offer)
        print("Sent DHCP Offer to " + pkt[Ether].src)

    elif DHCP in pkt and pkt[DHCP].options[0][1] == 3:
        print("Received DHCP Request from " + pkt[Ether].src)
        dhcp_ack = Ether(dst=pkt[Ether].src) / IP(src="192.168.1.1", dst="255.255.255.255") / UDP(sport=67,
                                                                                                  dport=68) / BOOTP(
            op=2, yiaddr=client_ip, siaddr=server_ip, xid=xid, chaddr=client_mac) / DHCP(
            options=[("message-type", "ack"), ("subnet_mask", subnet_mask), ("router", server_ip),
                     ('domain', 'example.com'),
                     ('name_server', dns_server_ip), "end"])
        sendp(dhcp_ack)
        print("Sent DHCP Ack to " + pkt[Ether].src)


if __name__ == '__main__':
    sniff(filter="udp and (port 67 or 68)", prn=handle_dhcp, iface="enp0s3")
