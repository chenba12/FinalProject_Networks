import os
import sys
from time import sleep

from scapy.all import *
from scapy.layers.dhcp import BOOTP, DHCP
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether
from app.client_sender import handle_dhcp_packets, send_dhcp_discover, get_client_ip, \
    get_dns_server_ip
import unittest
from dhcp.dhcp import broadcast, dns_name, subnet_mask, dns_server_ip

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestDHCP(unittest.TestCase):

    def test_ip(self):
        # send a DHCP discover packet tzo trigger the function
        send_dhcp_discover()

        # create a fake DHCP offer packet to test the function's response
        offer = Ether() / IP() / UDP(sport=67, dport=68) / BOOTP(yiaddr="192.168.1.100") / DHCP(
            options=[("message-type", 2), ("server_id", "192.168.1.1"), ("name_server", "8.8.8.8"),
                     ("yiaddr", "192.168.1.100"), "end"])

        # call the function with the fake packet
        handle_dhcp_packets(offer)

        # check that the function correctly updates the global variables dns_server_ip and client_ip
        assert get_client_ip() == "192.168.1.100"

    def test_dns_ip(self):
        client_mac = "00:11:22:33:44:55"
        client_ip = "192.168.1.100"
        server_ip = "192.168.1.1"
        xid = 123456789
        # create a fake DHCP offer packet to test the function's response
        ack = Ether(dst=client_mac) / IP(src=server_ip, dst=broadcast) / UDP(sport=67,
                                                                             dport=68) / BOOTP(
            op=2, yiaddr=client_ip, siaddr=server_ip, xid=xid, chaddr=client_mac) / DHCP(
            options=[("message-type", 5), ("subnet_mask", subnet_mask), ("router", server_ip),
                     ('domain', dns_name),
                     ('name_server', dns_server_ip), "end"])

        handle_dhcp_packets(ack)
        assert get_dns_server_ip() == "192.168.1.2"
