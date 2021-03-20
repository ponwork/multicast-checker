# Script will parse the input *.m3u playlist file and check all the channels inside.
# Please read the manual (run the script with -h parameter)
# 
# author: Yuri Ponomarev
# Github: https://github.com/ponwork/

import concurrent.futures
import argparse
import time
import socket
import struct
import select
import json
import re
import os
import platform
import subprocess
import sys
import smtplib
from email.mime.text import MIMEText

# Setup the command line argument parsing
parser = argparse.ArgumentParser(description='Script to check the IPTV UDP streams from m3u playlist')

parser.add_argument("--playlist",       help="Playlist *.m3u file with UDP streams",            required=True)
parser.add_argument("--nic",            help="network interface IP address with UDP stream",    required=False, default='0.0.0.0')
parser.add_argument("--udp_timeout",    help="Time to wait in seconds for the UPD port reply",  required=False, default=5)
parser.add_argument("--info_timeout",   help="Time to wait in seconds for the stream's info",   required=False, default=10)
parser.add_argument("--smtp_server",    help="SMTP server to send an email",                    required=False)
parser.add_argument("--smtp_port",      help="Port for SMTP server",                            required=False, default=25)
parser.add_argument("--sender",         help="email address for email sender",                  required=False)
parser.add_argument("--receivers",      help="emails of the receivers (space separated)",       required=False, nargs='+')

# ================
# Define functions
# ================

def get_ffprobe(address, port):
    """ To get the json data from ip:port """

    global args

    # Run the ffprobe with given IP and PORT with a given timeout to execute
    try:
        
        # Capture the output from ffprobe
        result = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_programs', f'udp://@{address}:{port}'], capture_output=True, text=True, timeout=args.info_timeout)
        
        # Convert the STDOUT to JSON
        json_string = json.loads(str(result.stdout))
    
    except:
        print(f'[*] No data found for {address}:{port}')
        return 0
    
    # Parse the JSON "PROGRAMS" section
    for program in json_string['programs']:
        
        # Parse the JSON "STEAMS" section
        for stream in program['streams']:

            # Check the stream via index data
            try:
                
                stream['index'] != ''
                
                # Check the stream's channel name
                try:

                    if program['tags']['service_name'] != '':
                        return program['tags']['service_name']
                    else:
                        return 1
                
                except:
                    return 1
            
            except:
                
                print(f'[*] No stream found for {address}:{port}')
                return 0

def playlist_parser(playlist):
    """ Function that returns a dictionary of UDP streams """
    
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
    
    return dictionary

def channel_checker(sock):
    """ Function to check the given UDP socket """

    global args

    ready = select.select([sock], [], [], args.udp_timeout)
    if ready[0]:
        sock.close()
        return 0
    else:
        return 1

def socket_creator(nic, address, port, os_name):
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
    # SO_REUSEPORT/SO_REUSEPORT socket option tells the kernel that even if this ip/port is busy
    # 1 representing a buffer
    #
    # For MacOS ('Darwin') use a reusable port, else -- reusable ip

    if os_name == 'Darwin':
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    else:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to the port that we know will receive multicast data
    sock.bind((nic, int(port)))
    
    # Tell the kernel that we are a multicast socket
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
    
    # Tell the kernel that we want to add ourselves to a multicast group
    # The address for the multicast group is the third param
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(address) + socket.inet_aton(nic))

    return sock

def mass_checker(channel):
    """ Function to mass check the channels in the dictionary """

    # Define global variables
    global os_name
    global channels_not_working

    # Check channel
    channel_address, channel_port = channels_dictionary[channel].split(':')
    sock = socket_creator(args.nic, channel_address, channel_port, os_name)
    result = channel_checker(sock)
    if result == 0:
        
        # Get the data of the possible stream
        info = get_ffprobe(channel_address, channel_port)
        
        if info == 1: # Stream captured but without channel name
                
            return f'[*] OK >>> Channel is working! >>> "{channel}" >>> No stream name found'

        elif info == 0:

            # Add the broken channel to the list
            channels_not_working += f'{channel_address}:{channel_port} - {channel}\n'
            return f'[*] Channel {channel} is not working'

        else: # Stream captured with channel name
            
            return f'[*] OK >>> Channel is working! >>> "{channel}" >>> Stream name: "{info}"'
    
    else:
        # Add the broken channel to the list
        channels_not_working += f'{channel_address}:{channel_port} - {channel}\n'
        return f'[*] Channel {channel} is not working'

def send_email(smtp_server, smtp_port, sender, receivers, channels_not_working):
    """ Function to send an email when IPTV channel failed to play """

    msg = MIMEText(f'The following channel(s) are not working:\n\n{channels_not_working}\n')
    msg['Subject'] = f'!!! IPTV issue !!!'
    msg['From'] = f'{sender}'
    msg['To'] = f'{receivers}'

    try:
        smtpObj = smtplib.SMTP(smtp_server, smtp_port)
        smtpObj.sendmail(sender, receivers, msg.as_string())
        print(f'[*] An email has been sent')
    except SMTPException:
        print(f'[*] Error: unable to send an email')

# ================
# End of functions
# ================

# Define the script arguments as a <args> variable
args = parser.parse_args()

# Check the OS name
os_name = platform.system()

# Check the user's input (playlist file)
if not os.path.isfile(args.playlist):
    print("[*] Please specify the correct playlist file's name!")
    sys.exit()

# Get the dictionary of UDP channels
channels_dictionary = playlist_parser(args.playlist)

# Check the user's input (email parameters)
email_set = 0
if args.smtp_server and args.smtp_port and args.sender and args.receivers:
    email_set = 1
else:
    print(f'[*] Email parameters are not defined.\n[*] Run the script with -h parameter for the details.\n')

# Main program
try:

    # Start timer:
    start = time.perf_counter()

    # Define a string for the non-working channels
    channels_not_working = ''

    # Run the checker as a multi-thread executor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = [executor.submit(mass_checker, channel) for channel in channels_dictionary]

        # Print the result:
        for item in concurrent.futures.as_completed(results):
            print(item.result())

    # Check the results and print/send the results
    if channels_not_working != '':

        # Print the list of broken channels
        print(f'\n[*] The following channel(s) are not working:\n\n{channels_not_working}')
        
        if email_set == 1:
            send_email(args.smtp_server, args.smtp_port, args.sender, args.receivers, channels_not_working)

    # Stop timer
    finish = time.perf_counter()

    # Print the execution time:
    total_time = round(finish - start, 0)
    print(f'\n[*] Finished in {total_time:,} second(s)')

except KeyboardInterrupt:
    print('\n[*] Script has been closed!')
    sys.exit()