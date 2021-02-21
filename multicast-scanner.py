# The script will scan the UDP IPs range (Default: 224.0.0.0/8).
# If the --playlst parameter defined the script will use all the unique ports for the scan
# Default port to scan (1234)
# Additional UDP ports can be defined via --udp_port argument(s). Example below:
# --udp_port 5500 --udp_port 5555

# TODO:
# Custom IP range ???

# Please read the manual (run the script with -h parameter) for more info

import argparse
import socket
import struct
import select
import smtplib
import re
import os
import sys
import ipaddress

# Setup the command line argument parsing
parser = argparse.ArgumentParser(description='Script to check the IPTV UDP streams from m3u playlist')

parser.add_argument("--playlist",		help="Playlist *.m3u file with UDP streams",			required=False)
parser.add_argument("--nic_ip",			help="network interface IP address with UDP stream",	required=False, default='')
parser.add_argument("--timeout",		help="Time to wait in seconds for the UPD stream", 		required=False, default=5)
parser.add_argument("--split",			help="The size of the sub-list of IPs to scan", 		required=False, default=131070)
parser.add_argument("--udp_port",		help="addtional UDP port to scan. Default: 1234",		required=False, default=['1234'], action='append')
parser.add_argument("--ip_range",		help="Range of IPs to scan. Default: 224.0.0.0/8",		required=False, default='224.0.0.0/8')

def ip_scanner(ip_list, udp_ports):
	""" Scan the given lists of IPs and ports """
	
	for ip in ip_list:
		for port in udp_ports:
			result = channel_checker(str(ip), port, args.nic_ip)
			if result == 0:
				print(f'[*] !!! Channel found !!! {str(ip)}:{port}')
				if args.playlist:
					if f'{str(ip)}:{port}' not in channels_dictionary:
						print(f'[*] Added to the playlist')
			else:
				print(f'[*] No stream found for: {str(ip)}:{port}')

def playlist_parser(playlist):
	""" Function that returns a dictionary of UDP streams"""
	
	# Defining the variables
	channel_name = ''
	channel_address = ''

	# Defininfg regular expression for strings
	channel_name_re = re.compile(r'(?<=#EXTINF:2,)(.*)(?=$)')
	channel_address_re = re.compile(r'(?<=@)(.*)(?=$)')

	# Create a dictionary
	dictionary = {}

	with open(playlist) as playlist:
		for counter, line in enumerate(playlist):
			if re.findall(channel_name_re ,line):
				channel_name = re.search(channel_name_re,line).group()
				channel_address = re.search(channel_address_re, playlist.readline()).group()
				dictionary[channel_name] = channel_address
	
	# Close the playlist file and return the dictionary with UDP streams
	playlist.close()
	
	return dictionary

def udp_pors_parser(channels_dictionary):
	""" Function to get the list of the unique ports fron the UDP channels dictionary """
	
	# Get the unique values of UDP channel:port lines
	upd_channels_ports = set(channels_dictionary.values())
	
	# Get the list of UDP ports
	udp_ports = []
	for item in upd_channels_ports:
		udp_port = item.split(':')[1]
		udp_ports.append(udp_port)

	# Get the unique list of UDP ports
	udp_ports = set(udp_ports)

	return udp_ports

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
		# Get the 1024 bytes of IPTV channel data
		data = sock.recv(1024)
		return 0
	else:
		return 1

# Define the script arguments as a <args> variable
args = parser.parse_args()

# Define the dictionary for UDP ports:
udp_ports = {}

# Check the data of the playlist file
if args.playlist:
	# Check the input playlist file
	if not os.path.isfile(args.playlist):
		print(f'[*] Please specify the correct file!')
		exit()
	else:
		print(f'[*] Playlist file: {args.playlist}!')

	# Get the dictionary of UDP channels
	channels_dictionary = playlist_parser(args.playlist)

	# Get the unique ports' numbers:
	udp_ports = udp_pors_parser(channels_dictionary)

# Add the user defined port(s)
if args.udp_port:
	udp_ports = list(udp_ports)
	udp_ports = udp_ports + args.udp_port
	udp_ports = set(udp_ports)

# Get the list of IPs to scan
try:
	ip_list = ipaddress.IPv4Network(args.ip_range)
except:
	print('\n[*] Please define a proper IP range.\n[*] >>> Example: 224.0.0.0/24\n')
	sys.exit()

# Calculating totals
print(f'[*] Calculating totals, please wait...')
total_IPs = len(list(ip_list))
total_ports = len(udp_ports)

# Scan the IPs range with the given ports:
try:
	print(f'\n[*] IP range to scan: {args.ip_range}')
	print(f'[*] Total IPs to scan: {"{:,}".format(total_IPs)}')
	print(f'[*] Total ports to scan for each IP: {total_ports}') 
	print(f"[*] Port(s) to scan: {','.join(udp_ports)}")
	print(f'[*] Timeout for UDP stream reply: {args.timeout} sec')
	print(f'\n[*] Total items to scan: {"{:,}".format(total_IPs*total_ports)}\n')
	
	# Number of IPs ranges after the division:
	ip_ranges = -(-total_IPs // int(args.split))

	# Print the notification if the IP range number is bigger than /15 subnet hosts
	if total_IPs >= int(args.split):
		print(f'[*] The IP range will be splitted for {ip_ranges} parts.')
		print(f'[*] Each part contain {"{:,}".format(args.split)} IPs\n')

	# Scanning time estimation:
	time_to_complete = int((total_IPs*total_ports*args.timeout)/ip_ranges)
	print(f'[*] Estimated maximum time to complete the task: {"{:,}".format(time_to_complete)} seconds')

	for i in range(0, len(list(ip_list)), int(args.split)):
		ip_list = list(ip_list)
		ip_list = ip_list[i:i + int(args.split)]
		ip_scanner(ip_list, udp_ports)

except KeyboardInterrupt:
	print('\n[*] Script has been closed!')
	sys.exit()