from scapy.layers.dns import DNS, DNSQR
from scapy.layers.inet import IP, UDP
from scapy.sendrecv import sr1


def dns_client(dns_server, domain_name):
    ip = IP(dst=dns_server)
    udp = UDP(sport=1024, dport=53)
    dns = DNS(rd=1, qd=DNSQR(qname=domain_name))
    response = sr1(ip / udp / dns, verbose=0, timeout=2)
    if response:
        response.show()


if __name__ == '__main__':
    dns_client('8.8.8.8', 'example.com')
