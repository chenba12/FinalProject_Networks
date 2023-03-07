from scapy.sendrecv import sniff

from rudp_client import udp_connect_to_server
from tcp_client import tcp_connect_to_app_server
from client_sender import send_dhcp_discover, filter_port, handle_ip, network_interface, \
    dns_packet_handle, dns_response, get_client_ip, get_dns_server_ip

if __name__ == '__main__':
    send_dhcp_discover()
    sniff(filter=filter_port, timeout=10, count=3, prn=handle_ip, iface=network_interface)
    print("IP address assigned to client: " + get_client_ip())
    print("DNS server IP: " + get_dns_server_ip())
    print("----------DHCP DONE----------")
    dns_packet_handle()
    sniff(filter=f"udp port 53 and src {get_dns_server_ip()}", prn=dns_response, timeout=10, count=1)
    print("----------DNS DONE----------")
    connect_to = input("Please choose connection TCP or UDP: ")
    if connect_to == "TCP":
        tcp_connect_to_app_server()
    elif connect_to == "UDP":
        udp_connect_to_server()
    else:
        print("Invalid protocol")
