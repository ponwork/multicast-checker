
# MULTICAST-CHECKER
> Research project

The project contains 2 scripts:

- [**multicast-checker.py**](https://github.com/ponwork/multicast-checker/blob/main/multicast-checker.py) : to check the status of the UDP channels in m3u playlist
- [**multicast-scanner.py**](https://github.com/ponwork/multicast-checker/blob/main/multicast-scanner.py) : to scan the UDP IP range and find the active streams

## Installing / Getting started

Both scripts are python3 compatible and use [FFprobe](https://ffmpeg.org/ffprobe.html) and [FFmpeg](https://www.ffmpeg.org/ffmpeg.html)

Please install before use: 

1. https://www.python.org/downloads/
2. https://www.ffmpeg.org/download.html

You can simply run the following examples to see how it works:

### **multicast-checker.py:**
```shell
python3 multicast-checker.py --playlist playlist.m3u
```
where *playlist.m3u* is a [M3U](https://en.wikipedia.org/wiki/M3U) file where all the UDP channels are listed

M3U file example:
```
#EXTM3U
#EXTINF:2,Info channel #1
udp://@233.99.65.1:1234
#EXTINF:2,Info channel #2
udp://@233.99.65.2:5500
#EXTINF:2,Info channel #3
udp://@233.99.65.3:1234
#EXTINF:2,Info channel #4
udp://@233.99.65.4:5500
#EXTINF:2,Info channel #5
udp://@233.99.65.5:1234
```

The script will scan all the schannels in the playlist.m3u using multithreading and return the results
The service_name metadata field from the UDP stream will be captured in advance.

Output example:
```
[*] Email parameters are not defined.
[*] Run the script with -h parameter for the details.

[*] Channel Info channel #2 is not working
[*] Channel Info channel #4 is not working
[*] Channel Info channel #3 is not working
[*] Channel Info channel #5 is not working
[*] OK >>> Channel is working! >>> "Info channel #1" >>> No stream name found

[*] The following channel(s) are not working:

233.99.65.2:5500 - Info channel #2
233.99.65.4:5500 - Info channel #4
233.99.65.3:1234 - Info channel #3
233.99.65.5:1234 - Info channel #5


[*] Finished in 7.0 second(s)
```

### **multicast-scanner.py**
```shell
python3 multicast-scanner.py --range 233.99.65.1/30
```

The script will scan the given UDP IP range using multithreading and return the results
The service_name metadata field from the UDP stream will be captured in advance.
If no service_name will be found the 10 secs sample will be captured.


Output example:
```
[*] IP range to scan: 233.99.65.0/30
[*] IPs to scan: 4
[*] Ports to scan for each IP: 1
[*] List of the port(s) to scan: 1234
[*] Timeout for UDP stream reply: 5 sec(s)
[*] Timeout for stream data collection: 10 sec(s)
[*] Sample lenght in seconds: 60 sec(s)

[*] Totals:
[*] Total items to scan: 4
[*] Total number of /32 subnets to scan (# of threads): 4
[*] Total number of hosts for each subnet to scan: 1 

[*] Estimated maximum time to complete the task: 50 seconds
[*] 0 day(s) 0 hour(s) 0 minute(s) 50 second(s)

[*] Found opened port 1234 for 233.99.65.1
[*] Scanning for 233.99.65.0/32 completed!
[*] Scanning for 233.99.65.2/32 completed!
[*] Scanning for 233.99.65.3/32 completed!
[*] !!! No channel name found for 233.99.65.1:1234 !!!
[*] !!! Channel added to the playlist. 233.99.65.1:1234 >>> 1 !!!
[*] Scanning for 233.99.65.1/32 completed!

[*] Recording the samples for unnamed channels...
[*] !!! Sample for 233.99.65.1:1234 captured !!!


[*] Finished in 14.0 second(s)
[*] 0.0 day(s) 0.0 hour(s) 0.0 minute(s) 14.0 second(s)

[*] Channels found: 1
[*] Resulting file: scan_results_range_233.99.65.0-30.m3u
```

Scripts were tested on Linux (Ubuntu 20.04) and MacOS (Big Sur, 11.2.2)


### Initial Configuration

You can find all the parameters of the scripts using the following:

```shell
python3 multicast-checker.py -h

--playlist"        "Playlist *.m3u file with UDP streams"             required: True
--nic"             "network interface IP address with UDP stream"     required: False default: '0.0.0.0'
--udp_timeout"     "Time to wait in seconds for the UPD port reply"   required: False default: 5
--info_timeout"    "Time to wait in seconds for the stream's info"    required: False default: 10
--smtp_server"     "SMTP server to send an email"                     required: False
--smtp_port"       "Port for SMTP server"                             required: False default: 25
--sender"          "email address for email sender"                   required: False
--receivers"       "emails of the receivers (space separated)"        required: False
```

```shell
python3 multicast-scanner.py -h
```

## Features

* checking the availability of the UDP channels;
* send the results via email;
* scan the UDP IP range and create a resulting M3U playlist using the metadata 'service_name'
* record the mp4 files as a samples for the unnamed channels


## Contributing

The **multicast-checker.py** project was created as a tool to monitor the ISP IPTV network and sent the alerts in case of channels outages.

The **multicast-scanner.py** project was created as a tool to discover all the available IPTV channels in the ISP's network.

Please feel free to comment/blame/suggest the further development

## Links

- Project homepage: https://github.com/ponwork/multicast-checker
- Issue tracker: https://github.com/ponwork/multicast-checker/issues

Data used:
- FFmpeg/FFprobe: https://github.com/FFmpeg/FFmpeg
- UDP Multicast: https://www.iana.org/assignments/multicast-addresses/multicast-addresses.xhtml
- Subnets division: https://www.davidc.net/sites/default/subnets/subnets.html

## Licensing

"The code in this project is licensed under MIT license."