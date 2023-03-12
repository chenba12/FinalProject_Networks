import subprocess
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
    use_script = 'n'
    iface = "enp0s3"
    if len(sys.argv) < 3:
        print("Using default values: network interface = enp0s3 Using script? n")
        print("Usage: sudo python3 ./app/client.py <network_interface> <Use script (y/n)>")
    else:
        iface = sys.argv[1]
        use_script = sys.argv[2]
        print(f"Network interface: {iface}")
        print(f"Using ip script: {use_script}")
        network_interface = iface

    send_dhcp_discover()
    sniff(filter=filter_port, timeout=10, count=3, prn=handle_dhcp_packets, iface=network_interface)
    print("IP address assigned to client: " + get_client_ip())
    print("DNS server IP: " + get_dns_server_ip())
    print("----------DHCP DONE----------")
    dns_packet_handle()
    sniff(filter=f"udp port 53 and src {get_dns_server_ip()}", prn=dns_response, timeout=10, count=1)
    print("----------DNS DONE----------")
    client_ip = ''
    if use_script == 'y':
        client_ip = get_client_ip()
        print("----------Running IP assignment script----------")
        subprocess.run(["./app/ip_script.sh", iface], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("----------IP assignment script Done----------")
    while True:
        connect_to = input("Please choose connection protocol TCP or RUDP: ")
        if connect_to == "TCP":
            tcp_connect_to_app_server(client_ip)
            break
        elif connect_to == "RUDP":
            udp_connect_to_server(client_ip)
            break
        else:
            print("Invalid protocol")
