#!/bin/bash
iface=${1:-enp0s3}

echo "Assigning IP addresses to interface: $iface"
echo "range 192.168.1.100 to 192.168.1.255"
for i in {100..255}; do
  sudo ip addr add 192.168.1."$i"/24 dev "$iface"
done
