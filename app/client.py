import sys

from scapy.sendrecv import sniff

from rudp_client import udp_connect_to_server
from tcp_client import tcp_connect_to_app_server
from client_sender import send_dhcp_discover, filter_port, handle_dhcp_packets, network_interface, \
    dns_packet_handle, dns_response, get_client_ip, get_dns_server_ip

# this file handles the client flow
# run this to start a new client

if __name__ == '__main__':
    print("----------Client UP---------")
    if len(sys.argv) < 2:
        print("Using default network interface = enp0s3")
        print("Usage: sudo python3 client.py <network_interface>")
    else:
        param1 = sys.argv[1]
        print(f"Network interface: {param1}")
        network_interface = param1
    send_dhcp_discover()
    sniff(filter=filter_port, timeout=10, count=3, prn=handle_dhcp_packets, iface=network_interface)
    print("IP address assigned to client: " + get_client_ip())
    print("DNS server IP: " + get_dns_server_ip())
    print("----------DHCP DONE----------")
    dns_packet_handle()
    sniff(filter=f"udp port 53 and src {get_dns_server_ip()}", prn=dns_response, timeout=10, count=1)
    print("----------DNS DONE----------")
    while True:
        connect_to = input("Please choose connection TCP or UDP: ")
        if connect_to == "TCP":
            tcp_connect_to_app_server()
            break
        elif connect_to == "UDP":
            udp_connect_to_server()
            break
        else:
            print("Invalid protocol")
