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

import concurrent.futures
import time
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

parser.add_argument("--range",          help="Range of IPs to scan.",                           required=True)
parser.add_argument("--size",           help="Size of the subnets to divide.",                  required=True)
parser.add_argument("--playlist",       help="Playlist *.m3u file with UDP streams",            required=False)
parser.add_argument("--nic",            help="network interface IP address with UDP stream",    required=False, default='0.0.0.0')
parser.add_argument("--timeout",        help="Time to wait in seconds for the UPD stream",      required=False, default=5)
parser.add_argument("--port",           help="addtional UDP port to scan. Default: 1234",       required=False, default=['1234'], nargs='+')
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
        file.write(f'#EXTINF:2,Channel #{id} Address: {ip}:{port}\n')

        #Add the channel address
        file.write(f'udp://@{ip}:{port}\n')

    print(f'[*] !!! Channel added to the playlist !!!')

    return 0

def ip_scanner(ip_list, port_list):
    """ Scan the given lists of IPs and ports """

    print(f'[*] >>> Scanning for {ip_list} started!')

    # Define the given dictionary
    global channels_dictionary

    counter = 0
    for ip in ip_list:
        for port in port_list:
            sock = socket_creator(args.nic, str(ip), port)
            result = channel_checker(sock)
            if result == 0:
                print(f'[*] !!! Channel found !!! {str(ip)}:{port}')
                if args.playlist:
                    if f'{str(ip)}:{port}' not in list(channels_dictionary.values()):
                        counter += 1
                        playlist_add(ip, port, counter)
                    else:
                        print(f'[*] The channel is already in the playlist')
                else:
                    counter += 1
                    playlist_add(ip, port, counter)
            else:
                print(f'[*] No stream found for: {str(ip)}:{port}')
    
    return f'[*] <<< Scanning for {ip_list} completed!'

def channel_checker(sock):
    """ Function to check the given UDP socket """

    global args

    ready = select.select([sock], [], [], args.timeout)
    if ready[0]:
        sock.close()
        return 0
    else:
        return 1


def socket_creator(nic, address, port):
    """ Creates a sockets for a given ports """

    # Create a UDP socket
    # AF_INET address family represented by a pair (host, port)
    # SOCK_DGRAM is a UDP socket type for datagram-based protocol
    # IPPROTO_UDP to set a UDP protocol type
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    
    # Allow multiple sockets to use the same PORT number
    # socket.setsockopt(level, optname, value: int)
    #
    # SOL_SOCKET is the socket layer/level itself
    # SO_REUSEPORT socket option tells the kernel that even if this port is busy
    # 1 representing a buffer
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    
    # Bind to the port that we know will receive multicast data
    sock.bind((nic, int(port)))
    
    # Tell the kernel that we are a multicast socket
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
    
    # Tell the kernel that we want to add ourselves to a multicast group
    # The address for the multicast group is the third param
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(address) + socket.inet_aton(nic))

    return sock

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
currentPath = os.path.dirname(os.path.realpath(__file__))

# Define the playlist file name
playlistFileName = f'scan_results_range_{args.range.split("/")[0]}-{args.range.split("/")[1]}.m3u'
playlistFile = os.path.join(currentPath, playlistFileName)

# Open the playlist file and add the first line (header)
with open(playlistFile, 'w') as file:
    file.write(f'#EXTM3U\n')

print(f'[*] Resulting file: {playlistFile}')
# # ===================================


# Devide the given IPs to the subnets
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

    # Start timer:
    start = time.perf_counter()

    # Run the scanner as a multi-thread executor
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(subnets)) as executor:
        results = [executor.submit(ip_scanner, subnet, port_list) for subnet in subnets]

        # Print the result:
        for item in concurrent.futures.as_completed(results):
            print(item.result())

    # Send an email with the resulting file
    if args.smtp_server and args.smtp_port and args.sender and args.receivers:
        send_email(args.smtp_server, args.smtp_port, args.sender, args.receivers, playlistFile, playlistFileName)

    # Stop timer
    finish = time.perf_counter()

    # Print the execution time:
    print(f'\n\nFinished in {round(finish - start, 2)} second(s)\n')

    sys.exit()

except KeyboardInterrupt:
    print('\n[*] Script has been closed!')
    sys.exit()