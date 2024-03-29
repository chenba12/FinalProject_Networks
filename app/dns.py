import sys
from time import sleep
from scapy.layers.dns import DNSQR, DNSRR, DNS
from scapy.layers.inet import IP, UDP
from scapy.all import *

from dhcp import get_network_interface

# This is the DNS server file here the client will ask for the ip of the sql app

# constants
app_name = "mySQLApp.com"
dns_server_ip = "192.168.1.2"
app_server_ip = "10.0.2.15"
iface = "enp0s3"


def dns_server(pkt) -> None:
    """
    captures dns packets and look for qname that equals to mySQLApp.com
    :param pkt: the dns packet that was captured
    """
    if pkt.haslayer(DNSQR):
        # Delay
        sleep(1)
        ip_src = pkt[IP].src
        dns_req = pkt[DNSQR].qname.decode().rstrip('.')
        if dns_req == app_name:
            print(f"---------DNS New Request---------")
            print(f"Details: from:{ip_src} for:{app_name}")
            # Respond with a DNS record for mySQLApp.com
            dns_resp = DNSRR(rrname=dns_req, rdata=app_server_ip, type="A")
            ip = IP(src=dns_server_ip, dst=ip_src)
            udp = UDP(sport=53, dport=pkt[UDP].sport)
            dns = DNS(id=pkt[DNS].id, qr=1, an=dns_resp)
            send(ip / udp / dns)
            print(f"Sent DNS Respond to {ip_src}")
            print(f"App Details: {app_name} {app_server_ip}")


if __name__ == '__main__':
    print(f"---------DNS server UP---------")
    if len(sys.argv) < 3:
        print("Using default network interface = enp0s3")
        print("Using default Application server IP = 10.0.2.15")
        print("Usage: sudo python3 ./app/dns.py <network_interface> <app_server_ip>")
    else:
        iface = sys.argv[1]
        app_server_ip = sys.argv[2]
        print(f"Network interface: {iface}")
        print(f"Application server IP: {app_server_ip}")
    sniff(filter='udp port 53', prn=dns_server)
