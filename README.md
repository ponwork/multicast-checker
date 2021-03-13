# multicast-checker
To check the IPTV channels streams (UDP based)

# multicast-scanner-plus
The script will scan the UDP IPs range for the given ports (default '1234').
As a result the resulting m3u file will be created.

If the --playlst parameter with the existing m3u file is defined the script will use all the unique ports from it
Additional UDP ports can be defined via --port argument(s). Example below:
--port 5500 5555
Please read the manual (run the script with -h parameter) for more info

Data used:
- https://www.iana.org/assignments/multicast-addresses/multicast-addresses.xhtml
- https://www.davidc.net/sites/default/subnets/subnets.html
