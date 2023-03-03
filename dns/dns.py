from time import sleep
from scapy.layers.dns import DNSQR, DNSRR, DNS
from scapy.layers.inet import IP, UDP
from scapy.sendrecv import send, sniff

network_interface = "enp0s3"
app_name = "mySQLApp.com"
dns_server_ip = "192.168.1.2"
app_server_ip = "10.0.2.15"


def dns_server(pkt):
    if pkt.haslayer(DNSQR):
        sleep(1)
        ip_src = pkt[IP].src
        dns_req = pkt[DNSQR].qname.decode().rstrip('.')
        if dns_req == app_name:
            print(f"Received DNS Request from {ip_src}")
            # Respond with a DNS record for mySQLApp.com
            dns_resp = DNSRR(rrname=dns_req, rdata=app_server_ip)
            udp = UDP(sport=53, dport=pkt[UDP].sport)
            dns = DNS(id=pkt[DNS].id, qr=1, an=dns_resp)
            ip = IP(src=dns_server_ip, dst=ip_src)
            send(ip / udp / dns)
            print(f"Sent DNS Respond to {ip_src}")


if __name__ == '__main__':
    pkt = sniff(filter='udp port 53', prn=dns_server)
