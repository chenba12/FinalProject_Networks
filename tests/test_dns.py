import os
import sys

from scapy.layers.dns import DNSRR, DNS
from scapy.layers.inet import IP, UDP
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.client_sender import app_server_name, dns_response
from app.dhcp import dns_server_ip


class TestDNS(unittest.TestCase):

    def test_dns_response(self):
        app_server_ip = "10.0.2.15"
        dns_resp = DNSRR(rrname=f"{app_server_name}.", rdata=app_server_ip, type="A")
        ip = IP(src=dns_server_ip, dst="192.168.1.100")
        udp = UDP(sport=53, dport=20961)
        dns = DNS(id=0xAAAA, qr=1, an=dns_resp)
        pkt = ip / udp / dns
        dns_response(pkt)
        assert app_server_ip == "10.0.2.15"


if __name__ == '__main__':
    unittest.main()
