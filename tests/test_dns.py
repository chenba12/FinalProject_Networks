from time import sleep
from scapy.layers.dns import DNSQR, DNSRR, DNS
from scapy.layers.inet import IP, UDP
from scapy.sendrecv import send, sniff
import unittest
from app.client_sender import app_server_name, dns_response
from dhcp.dhcp import dns_server_ip


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