# Script to scan UPD addresses to find the media streams
# 
# author: Yuri Ponomarev
# Github: https://github.com/ponwork/

import concurrent.futures
import time
import argparse
import socket
import struct
import select
import os
import platform
import subprocess
import json
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
parser.add_argument("--udp_timeout",    help="Time to wait in seconds for the UPD port reply",  required=False, default=5)
parser.add_argument("--port",           help="addtional UDP port to scan. Default: 1234",       required=False, default=['1234'], nargs='+')
parser.add_argument("--sample_sec",     help="Sample lenght in seconds",                        required=False, default=60)
parser.add_argument("--info_timeout",   help="Time to wait in seconds for the stream's info",   required=False, default=10)
parser.add_argument("--smtp_server",    help="SMTP server to send an email",                    required=False)
parser.add_argument("--smtp_port",      help="Port for SMTP server",                            required=False, default=25)
parser.add_argument("--sender",         help="email address for email sender",                  required=False)
parser.add_argument("--receivers",      help="emails of the receivers (space separated)",       required=False, nargs='+')

# Define the variable for the channels dictionary
channels_dictionary = []

# Define the variable for the list of the channels without names 
unnamed_channels_dictionary = []

# ================
# Define functions
# ================

def seconds_humanize(input_seconds):
    """ Convert seconds to Human readable format"""

    days = input_seconds // (24 * 3600)
    input_seconds = input_seconds % (24 * 3600)
    hours = input_seconds // 3600
    input_seconds %= 3600
    minutes = input_seconds // 60
    input_seconds %= 60
    seconds = input_seconds

    return days, hours, minutes, seconds

def get_ffmpeg_sample(address, port):
    """ To get the stream sample """

    global args

    try:
        subprocess.run([f'ffmpeg -v quiet -y -i udp://@{address}:{port} -t {args.sample_sec} sample_{address}-{port}.mp4'], \
                        shell=True, stdin=None, stdout=None, stderr=None)
    except:
        print(f'[*] !!! Error with saving the file: sample_{address}-{port}.mp4 !!!')
        sys.exit()   

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

            # Check the stream via codec_type data
            try:
                
                stream['codec_type'] != ''
                
                # Check the stream's channel name
                try:

                    if program['tags']['service_name'] != '':
                        return program['tags']['service_name']
                    else:
                        print(f'[*] !!! No channel name found for {address}:{port} !!!')
                        return 1
                
                except:
                    
                    print(f'[*] !!! No channel name found for {address}:{port} !!!')
                    return 1
            
            except:
                
                print(f'[*] No stream found for {address}:{port}')
                return 0

def create_file(range):
    """ Prepare the resulting playlist file """

    #define the current directory
    currentPath = os.path.dirname(os.path.realpath(__file__))

    # Define the playlist file name
    playlistFileName = f'scan_results_range_{range.split("/")[0]}-{range.split("/")[1]}.m3u'
    playlistFile = os.path.join(currentPath, playlistFileName)

    # Open the playlist file and add the first line (header)
    with open(playlistFile, 'w') as file:
        file.write(f'#EXTM3U\n')

    return playlistFileName, playlistFile

def playlist_add(ip, port, name):
    """ Add the given IP and port to the playlist file"""

    # Define the full name/path to the playlist file
    global playlistFile

    # Define the given dictionary
    global channels_dictionary

    # Check the name variable%
    if type(name) is int:
        channel_string = f'#EXTINF:2,Channel: {ip}:{port}\n'
    else:
        channel_string = f'#EXTINF:2,{name}\n'

    
    # Open the file
    with open(playlistFile, 'a') as file:
        
        # Check if the playlist was provided:
        if args.playlist:
            if f'{str(ip)}:{port}' not in list(channels_dictionary.values()):
                
                # Add the channel name line
                file.write(channel_string)

                #Add the channel address
                file.write(f'udp://@{ip}:{port}\n')

                print(f'[*] !!! Channel added to the playlist. {ip}:{port} >>> {name} !!!')

                return 0
                            
            else:
                print(f'[*] The channel is already in the playlist: {ip}:{port} >>> {name}')
                return 0
        
        # Add the channel name line
        file.write(channel_string)

        #Add the channel address
        file.write(f'udp://@{ip}:{port}\n')


    print(f'[*] !!! Channel added to the playlist. {ip}:{port} >>> {name} !!!')

    return 0

def ip_scanner(ip_list, port_list):
    """ Scan the given lists of IPs and ports """

    for ip in ip_list:
        for port in port_list:
            sock = socket_creator(args.nic, str(ip), port, os_name)
            result = channel_checker(sock)
            if result == 0:
                
                print(f'[*] Found opened port {port} for {str(ip)}')
                
                # Get the data of the possible stream
                info = get_ffprobe(ip, port)

                if info == 1: # Stream captured but without channel name
                    
                    playlist_add(ip, port, info)
                    unnamed_channels_dictionary.append(f'{ip}:{port}')
                    
                    return 0

                elif info != 0: # Stream captured with channel name
                    playlist_add(ip, port, info)

            # else:
            #     print(f'[*] No stream found for: {str(ip)}:{port}')
    
    return f'[*] Scanning for {ip_list} completed!'

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
        print(f'[*] An email has been sent to {receivers}')
    except SMTPException as error:
        print(f'[*] Error: unable to send an email\n\n{error}\n')

# ================
# End of functions
# ================

# Define the script arguments as a <args> variable
args = parser.parse_args()

# Check the OS name
os_name = platform.system()

# Define the dictionary for UDP ports:
port_list = {}

# Create a resulting playlist file:
playlistFileName, playlistFile = create_file(args.range)

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
print(f'[*] Timeout for UDP stream reply: {args.udp_timeout} sec(s)')
print(f'[*] Timeout for stream data collection: {args.info_timeout} sec(s)')
print(f'[*] Sample lenght in seconds: {args.sample_sec} sec(s)')
print(f'\n[*] Totals:')
print(f'[*] Total items to scan: {total_IPs*total_ports:,}')
print(f'[*] Total number of /{args.size} subnets to scan (# of threads): {len(subnets)}')
print(f'[*] Total number of hosts for each subnet to scan: {int(total_IPs/len(subnets))} \n')

# Scanning time estimation:
time_to_complete = int((total_IPs/len(subnets))*total_ports*int(args.udp_timeout)*int(args.info_timeout))

print(f'[*] Estimated maximum time to complete the task: {time_to_complete:,} seconds')

# Conver to humain readable
days, hours, minutes, seconds = seconds_humanize(time_to_complete)
print(f'[*] {days} day(s) {hours} hour(s) {minutes} minute(s) {seconds} second(s)\n')

# Check that FFmpeg/FFprobe are installed
try:
    subprocess.call(['ffprobe', '-v', 'quiet'])
    subprocess.call(['ffmpeg', '-v', 'quiet'])
except FileNotFoundError:
    print('[*] ffmpeg and ffprobe are not installed! Please install first: https://ffmpeg.org/')
    sys.exit()

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

    # Record the samples of the unnamed channels
    if unnamed_channels_dictionary:
        print(f'\n[*] Recording the samples for unnamed channels...')
        for channel in unnamed_channels_dictionary:
            address, port = channel.split(':')
            get_ffmpeg_sample(address, port)
            print(f'[*] !!! Sample for {address}:{port} captured !!!')

    # Send an email with the resulting file
    if args.smtp_server and args.smtp_port and args.sender and args.receivers:
        send_email(args.smtp_server, args.smtp_port, args.sender, args.receivers, playlistFile, playlistFileName)

    # Stop timer
    finish = time.perf_counter()

    # Print the execution time:
    total_time = round(finish - start, 0)
    print(f'\n\n[*] Finished in {total_time:,} second(s)')

    # Conver to humain readable
    days, hours, minutes, seconds = seconds_humanize(total_time)
    print(f'[*] {days} day(s) {hours} hour(s) {minutes} minute(s) {seconds} second(s)\n')

    # Count the results
    count_results = len(open(playlistFile).readlines())
    
    # Print the results and remove empty files if no channels found:
    if count_results < 3:
        print(f'[*] No channels found\n')
        os.remove(playlistFile)
    else:
        print(f'[*] Channels found: {int((count_results - 1)/2)}')
        print(f'[*] Resulting file: {playlistFile}\n')
    sys.exit()

except KeyboardInterrupt:
    print('\n[*] Script has been closed!')
    sys.exit()