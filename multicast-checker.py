# Script will parse the input *.m3u playlist file and check all the channels inside.
# In case if the channel is not working (no data eceived) and email can be send.
# Please read the manual (run the script with -h parameter)

import argparse
import socket
import struct
import select
import smtplib
import re
import time
import os
from email.mime.text import MIMEText

# Setup the command line argument parsing
parser = argparse.ArgumentParser(description='Script to check the IPTV UDP streams from m3u playlist')

parser.add_argument("--playlist",		help="Playlist *.m3u file with UDP streams",			required=True)
parser.add_argument("--timeout",		help="Time to wait before checks in seconds",			default=600)
parser.add_argument("--smtp_server",	help="SMTP server to send an email",					required=False)
parser.add_argument("--smtp_port",		help="Port for SMTP server", 							default=25)
parser.add_argument("--sender",			help="email address for email sender",					required=False)
parser.add_argument("--receivers",		help="emails of the receivers (comma separated)",		required=False, action='append')
parser.add_argument("--nic_ip",			help="network interface IP address with UDP stream",	default='', required=False)

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

	# Check that socket is ready with 1 sec timeout
	ready = select.select([sock], [], [], 1)

	if ready[0]:
		# Get the 1024 bytes of IPTV channel data
		data = sock.recv(1024)
		return 0
	else:
		return 1

def send_email(smtp_server, smtp_port, sender, receivers, channel_name, channel_addr, channel_port):
	""" Function to send an email when IPTV channel failed to play"""

	msg = MIMEText(f'The channel "{channel_name}" is not working\nAddress: {channel_addr}:{channel_port}')
	msg['Subject'] = f'IPTV stream issue for "{channel_name}" channel'
	msg['From'] = f'{sender}'
	msg['To'] = f'{receivers}'

	try:
		smtpObj = smtplib.SMTP(smtp_server, smtp_port)
		smtpObj.sendmail(sender, receivers, msg.as_string())
		print(f'[*] An email has been sent')
	except SMTPException:
		print(f'[*] Error: unable to send an email')


# Define the script arguments as a <args> variable
args = parser.parse_args()

# Check the input playlist file
if not os.path.isfile(args.playlist):
    print('Please specify the correct file!')
    exit()

# Get the dictionary of UDP channels
channels_dictionary = playlist_parser(args.playlist)

# Main program's loop
while True:
	# Check each channel in dictionary
	for channel in channels_dictionary:
		channel_address, channel_port = channels_dictionary[channel].split(':')
		result = channel_checker(channel_address, channel_port, args.nic_ip)
		if result == 0:
			print(f'[*] OK >>> Channel "{channel}" is working!')
		else:
			print(f'[*] !!! PROBLEM !!! Channel "{channel}" is not working!')
			send_email(args.smtp_server, args.smtp_port, args.sender, args.receivers, channel, channel_address, channel_port)
	
	# Wait 10 minutes (default) to repeat
	print(f'\nWaiting for {args.timeout} second(s) to repeat the check...\n')
	time.sleep(int(args.timeout))