# The script will scan the UDP IPs range (Default: 224.0.0.0/8).
# If the --playlst parameter defined the script will use all the unique ports for the scan
# Default port to scan (1234)
# Additional UDP ports can be defined via --port argument(s). Example below:
# --port 5500 5555
# Please read the manual (run the script with -h parameter) for more info
#
# Data used:
# - https://www.iana.org/assignments/multicast-addresses/multicast-addresses.xhtml
# - https://www.davidc.net/sites/default/subnets/subnets.html
# - https://www.youtube.com/watch?v=IEEhzQoKtQU

import argparse
import socket
import struct
import select
import os
import re
import sys
import ipaddress
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Setup the command line argument parsing
parser = argparse.ArgumentParser(description='Script to check the IPTV UDP streams from m3u playlist')

parser.add_argument("--playlist",       help="Playlist *.m3u file with UDP streams",            required=False)
parser.add_argument("--nic",            help="network interface IP address with UDP stream",    required=False, default='')
parser.add_argument("--timeout",        help="Time to wait in seconds for the UPD stream",      required=False, default=5)
parser.add_argument("--port",           help="addtional UDP port to scan. Default: 1234",       required=False, default=['1234'], nargs='+')
parser.add_argument("--range",          help="Range of IPs to scan. Default: 233.252.0.0/14",   required=False, default='233.252.0.0/14')
parser.add_argument("--size",           help="Size of the subnets to divide. Default: 24",      required=False, default=24)
parser.add_argument("--smtp_server",    help="SMTP server to send an email",                    required=False)
parser.add_argument("--smtp_port",      help="Port for SMTP server",                            required=False, default=25)
parser.add_argument("--sender",         help="email address for email sender",                  required=False)
parser.add_argument("--receivers",      help="emails of the receivers (space separated)",       required=False, nargs='+')

# Define the variable for the dictionary
channels_dictionary = []

# Define functions
# ================

def playlist_add(ip, port, id):
    """ Add the given IP and port to the playlist file"""
    
    # Define the full name/path to the playlist file
    global playlistFile

    # Open the file
    with open(playlistFile, 'a') as file:

        # Add the channel name line
        file.write(f'#EXTINF:2,Channel #{id}\n')

        #Add the channel address
        file.write(f'udp://@{ip}:{port}\n')

    print(f'[*] !!! Channel added to the playlist !!!\n')

    return 0

def ip_scanner(ip_list, port_list):
    """ Scan the given lists of IPs and ports """

    # Define the given dictionary
    global channels_dictionary

    counter = 0
    for ip in ip_list:
        for port in port_list:
            result = channel_checker(str(ip), port, args.nic)
            if result == 0:
                print(f'\n[*] !!! Channel found !!! {str(ip)}:{port}')
                if args.playlist:
                    if f'{str(ip)}:{port}' not in list(channels_dictionary.values()):
                        counter += 1
                        playlist_add(ip, port, counter)
                    else:
                        print(f'[*] The channel is already in the playlist\n')
                else:
                    counter += 1
                    playlist_add(ip, port, counter)
            else:
                print(f'[*] No stream found for: {str(ip)}:{port}')
    return 0

def channel_checker(channel_address, channel_port, nic):
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

    sock.bind((nic, int(channel_port)))

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

    # Open the playlist file and write the data to the dictionary
    with open(playlist) as playlist:
        for counter, line in enumerate(playlist):
            if re.findall(channel_name_re ,line):
                channel_name = re.search(channel_name_re,line).group()
                channel_address = re.search(channel_address_re, playlist.readline()).group()
                dictionary[channel_name] = channel_address
    
    return dictionary

def udp_pors_parser(channels_dictionary):
    """ Function to get the list of the unique ports fron the UDP channels dictionary """
    
    # Get the unique values of UDP channel:port lines
    upd_channels_ports = set(channels_dictionary.values())
    
    # Get the list of UDP ports
    port_list = []
    for item in upd_channels_ports:
        port = item.split(':')[1]
        port_list.append(port)

    # Get the unique list of UDP ports
    port_list = set(port_list)

    return port_list

def send_email(smtp_server, smtp_port, sender, receivers, attachment, attachment_name):
    """ Function to send an email with an attached file of the scan result """

    global args

    # Define the email's main parts
    msg = MIMEMultipart()
    msg['Subject'] = f'IPTV scan results for "{str(args.range)}" range'
    msg['From'] = f'{sender}'
    msg['To'] = f'{receivers}'
    
    # Email message's body
    msg_body = f'The following channel(s) were found (see attached)\n{attachment_name}\n'
    msg_body = MIMEText(msg_body) # convert the body to a MIME compatible string
    msg.attach(msg_body) # attach it to your main message

    # Add attachment file
    email_attach = MIMEText(open(attachment).read())
    email_attach.add_header('Content-Disposition', 'attachment', filename=attachment_name)           
    msg.attach(email_attach)

    try:
        smtpObj = smtplib.SMTP(smtp_server, smtp_port)
        smtpObj.sendmail(sender, receivers, msg.as_string())
        print(f'[*] An email has been sent')
    except SMTPException:
        print(f'[*] Error: unable to send an email')

# ================
# End of functions

# Define the script arguments as a <args> variable
args = parser.parse_args()

# Define the dictionary for UDP ports:
port_list = {}

# Check the data of the playlist file
if args.playlist:
    # Check the input playlist file
    if not os.path.isfile(args.playlist):
        print(f'[*] Please specify the correct file!')
        exit()
    else:
        print(f'[*] Playlist file: {args.playlist}')

    # Get the dictionary of UDP channels
    channels_dictionary = playlist_parser(args.playlist)

    # Get the unique ports' numbers:
    port_list = udp_pors_parser(channels_dictionary)

# Add the user defined port(s)
if args.port:
    port_list = list(port_list)
    port_list = port_list + args.port
    port_list = set(port_list)

# Get the list of IPs to scan
try:
    ip_list = ipaddress.IPv4Network(args.range)
except:
    print(f'\n[*] Please define a proper IP range.\n[*] >>> Example: 224.0.0.0/24\n')
    exit()

# Check that the IPs are multicast
if ip_list.is_multicast: 
    pass
else:
    print(f'[*] IPs provided are not multicase. Please try again.')
    sys.exit()

# # Prepare the resulting playlist file
# # ===================================
# # define the current directory
# currentPath = os.path.dirname(os.path.realpath(__file__))

# # Define the playlist file name
# playlistFileName = f'scan_results_range_{args.range.split("/")[0]}-{args.range.split("/")[1]}.m3u'
# playlistFile = os.path.join(currentPath, playlistFileName)

# # Open the playlist file and add the first line (header)
# with open(playlistFile, 'w') as file:
#     file.write(f'#EXTM3U\n')

# print(f'[*] Resulting file: {playlistFile}')
# # ===================================


# Devide the given IPs to the /24 subnets
try:
    subnets = ip_list.subnets(new_prefix=int(args.size))
    subnets = list(subnets)
except:
    print(f'[*] ERROR: the new prefix --size: "{args.size}" must be longer than the given IPs subnet: "/{ip_list.prefixlen}"\n')
    sys.exit()

# Calculating and printing the totals
total_IPs = ip_list.num_addresses
total_ports = len(port_list)

print(f'\n[*] IP range to scan: {args.range}')
print(f'[*] IPs to scan: {total_IPs:,}')
print(f'[*] Ports to scan for each IP: {total_ports}') 
print(f"[*] List of the port(s) to scan: {', '.join(port_list)}")
print(f'[*] Timeout for UDP stream reply: {args.timeout} sec(s)')
print(f'\n[*] Totals:')
print(f'[*] Total items to scan: {total_IPs*total_ports:,}')
print(f'[*] Total number of /{args.size} subnets to scan (# of threads): {len(subnets)}')
print(f'[*] Total number of hosts for each subnet to scan: {int(total_IPs/len(subnets))} \n')

# Scanning time estimation:
time_to_complete = int((total_IPs/len(subnets))*total_ports*int(args.timeout))

print(f'[*] Estimated maximum time to complete the task: {time_to_complete:,} seconds')

# Scanning time estimation. Human readable
day = time_to_complete // (24 * 3600)
time_to_complete = time_to_complete % (24 * 3600)
hour = time_to_complete // 3600
time_to_complete %= 3600
minutes = time_to_complete // 60
time_to_complete %= 60
seconds = time_to_complete

print(f'[*] {day} day(s) {hour} hour(s) {minutes} minute(s) {seconds} second(s)\n')

# Scan the IPs range with the given ports:
try:

    # Run the scanner
    #ip_scanner(ip_list, port_list)

    # Send an email with the resulting file
    if args.smtp_server and args.smtp_port and args.sender and args.receivers:
        send_email(args.smtp_server, args.smtp_port, args.sender, args.receivers, playlistFile, playlistFileName)

    sys.exit()

except KeyboardInterrupt:
    print('\n[*] Script has been closed!')
    sys.exit()