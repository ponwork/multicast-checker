#  sudo -u super /Applications/VLC.app/Contents/MacOS/VLC -vvv --intf dummy /Users/super/Movies/web/stewart-lee.mp4 --sout udp://233.99.65.1:1234 --loop

import socket
import struct
import select

MCAST_GRP = '233.99.65.1'
MCAST_PORT = 1234
buff = 1024
timeout = 1


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

sock.bind(('', MCAST_PORT))

# Pack and format the socket data as following:
# '4sl' format: 4 - nember of bytes, s - char[] to bytes, l - long to integer
# inet_aton: Convert an IPv4 address from to 32-bit packed binary format
# INADDR_ANY used to bind to all interfaces
mreq = struct.pack('4sl', socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

# REconfigure the socket
# IPPROTO_IP: apply IP protocol type
# IP_ADD_MEMBERSHIP: recall that you need to tell the kernel which multicast groups you are interested in
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Apply non-blocking mode
sock.setblocking(0)



while True:
	# Check that socket is ready
	ready = select.select([sock], [], [], timeout)
	
	if ready[0]:
		data = sock.recv(buff)
		print('Channel is working')
	else:
		print('No data for the channel')