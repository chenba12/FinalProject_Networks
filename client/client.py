import time

from scapy.all import *
from scapy.layers.dhcp import DHCP, BOOTP
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether

client_mac = bytes.fromhex(" ".join(["08", "00", "27", "11", "11", "11"]))
client_ip = "0.0.0.0"
dns_ip = ""


def handle_ip(pkt):
    global dns_ip, client_ip

    time.sleep(1)
    if DHCP in pkt and pkt[DHCP].options[0][1] == 2:
        print("Received DHCP Offer from " + pkt[Ether].src)
        ip = pkt[BOOTP].yiaddr
        mac = pkt[Ether].src
        dhcp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / IP(src="0.0.0.0", dst="255.255.255.255") / UDP(sport=68,
                                                                                                       dport=67) / BOOTP(
            op=1, chaddr=mac) / DHCP(
            options=[("message-type", "request"), ("requested_addr", ip), ("server_id", pkt[IP].src), "end"])
        sendp(dhcp_request)
        print("Sent DHCP Request to " + pkt[IP].src)
    if DHCP in pkt and pkt[DHCP].options[0][1] == 5:
        if pkt.haslayer(DHCP):
            for option in pkt[DHCP].options:
                if option[0] == "name_server":
                    dns_ip = option[1]
        client_ip = pkt[BOOTP].yiaddr
        print("IP address assigned to client: " + client_ip)
        print("DNS server IP: " + dns_ip)
        return True


def send_dhcp_discover():
    dhcp_discover = Ether(src=client_mac, dst="ff:ff:ff:ff:ff:ff") / \
                    IP(src="0.0.0.0", dst="255.255.255.255") / \
                    UDP(sport=68, dport=67) / \
                    BOOTP(op=1, chaddr=client_mac) / \
                    DHCP(options=[("message-type", "discover"),
                                  ("client_id", client_mac),
                                  ("requested_addr", client_ip),
                                  ("option_list", [6, 3]),  # Request DNS server IP and Router IP
                                  "end"])
    sendp(dhcp_discover, iface="enp0s3")


if __name__ == '__main__':
    send_dhcp_discover()
    sniff(filter="udp and (port 67 or 68)", timeout=10, count=3, prn=handle_ip, iface="enp0s3")
    print("hey :)")
