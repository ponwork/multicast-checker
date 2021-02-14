import re
import os

currentPath = os.path.dirname(os.path.realpath(__file__))
playlist_file = 'ghe-iptv-channels-westcall-vlan-145.m3u'
playlist = os.path.join(currentPath, playlist_file)

# Defining the variables
channel_name = ''
channel_address = ''

# Defininfg regular expression for strings
channel_name_re = re.compile(r'(?<=#EXTINF:2,)(.*)(?=$)')
channel_address_re = re.compile(r'(?<=@)(.*)(?=$)')
#channel_address_re = re.compile(r'(?<=@)(.*)(?=:)')
#channel_port_re = re.compile(r'(?:)(?:[0-9]+)$')

# Create a dictionary
dictionary = {}

with open(playlist) as playlist:
	for counter, line in enumerate(playlist):
		if re.findall(channel_name_re ,line):
			channel_name = re.search(channel_name_re,line).group()
			channel_address = re.search(channel_address_re, playlist.readline()).group()
			dictionary[channel_name] = channel_address
		else: pass

print(dictionary)