# Subprocess for "multicast-scanner.py" script
#
# The script will scan the given UDP IPs range and ports

# Please read the manual (run the script with -h parameter) for more info

import argparse
import socket
import struct
import select
import re
import os
import sys

# Setup the command line argument parsing
parser = argparse.ArgumentParser(description='Subworker script to check the IPTV UDP streams from m3u playlist')

parser.add_argument("--ip_list",    help="List of the IP addresses to scan",    required=True, nargs='+')
parser.add_argument("--port_list",  help="List of the ports to scan",           required=True, nargs='+')
parser.add_argument("--nic_ip",     help="network interface IP",                required=False, default='')
parser.add_argument("--id",         help="Subprocess ID",                       required=True)

def ip_scanner(ip_list, port_list, id):
    """ Scan the given lists of IPs and ports """
    
    # Convert the given list of single string with IPs to the list of IPs
    ip_list = ip_list[0].split(' ')

    for ip in ip_list:
        for port in port_list:
            result = channel_checker(str(ip), port, args.nic_ip)
            if result == 0:
                print(f'\n[*] !!! Channel found !!! {str(ip)}:{port}')
                print(f'[*] !!! Channel added to the playlist !!!\n')
            else:
                print(f'[*] No stream found for: {str(ip)}:{port}')

    return print(f'[*] Subprocess #{id} completed')

def channel_checker(channel_address, channel_port, nic_ip):
    """ Function to check the given UDP stream """

    # Creating the socket
    # AF_INET address family represented by a pair (host, port)
    # SOCK_DGRAM is a UDP socket type for datagram-based protocol
    # IPPROTO_UDP to set a UDP protocol type
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Configuring the socket
    # socket.setsockopt(level, optname, value: int)
    #
    # SOL_SOCKET is the socket layer/level itself
    # SO_REUSEADDR socket option tells the kernel that even if this port is busy
    # 1 representing a buffer
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind((nic_ip, int(channel_port)))

    # Pack and format the socket data as following:
    # '4sl' format: 4 - nember of bytes, s - char[] to bytes, l - long to integer
    # inet_aton: Convert an IPv4 address from to 32-bit packed binary format
    # INADDR_ANY used to bind to all interfaces
    mreq = struct.pack('4sl', socket.inet_aton(channel_address), socket.INADDR_ANY)

    # REconfigure the socket
    # IPPROTO_IP: apply IP protocol type
    # IP_ADD_MEMBERSHIP: recall that you need to tell the kernel which multicast groups you are interested in
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # Apply non-blocking mode
    sock.setblocking(0)

    # Check that socket is ready with 10 sec timeout
    ready = select.select([sock], [], [], 5)

    if ready[0]:
        return 0
    else:
        return 1

# Define the script arguments as a <args> variable
args = parser.parse_args()

try:
    print(f'\n\n[*] Subprocess #{args.id} started:')
    ip_scanner(args.ip_list, args.port_list, args.id)
    exit()
except KeyboardInterrupt:
    print('\n[*] Script has been closed!')
    sys.exit()