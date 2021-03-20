
# MULTICAST-CHECKER
> Research project

The project contains 2 scripts:

- **multicast-checker.py** : to check the status of the UDP channels in m3u playlist
- **multicast-scanner.py** : to scan the UDP IP range and find the active streams

## Installing / Getting started

Both scripts are python3 compatible and use [FFprobe](https://ffmpeg.org/ffprobe.html) and [FFmpeg](https://www.ffmpeg.org/ffmpeg.html)
Please install: https://www.ffmpeg.org/download.html

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

The script will scan all the schannels in the playlist.m3u and return the results
(the service_name metadata field from the UDP stream will be captured in advance)

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
python3 multicast-scanner.py --range 233.0.0.0/24
```



Scripts are tested on Linux (Ubuntu 20.04) and MacOS (Big Sur, 11.2.2)


### Initial Configuration

Some projects require initial configuration (e.g. access tokens or keys, `npm i`).
This is the section where you would document those requirements.


## Features

What's all the bells and whistles this project can perform?
* What's the main functionality
* You can also do another thing
* If you get really randy, you can even do this

## Configuration

Here you should write what are all of the configurations a user can enter when
using the project.

#### Argument 1
Type: `String`  
Default: `'default value'`

State what an argument does and how you can use it. If needed, you can provide
an example below.

Example:
```bash
awesome-project "Some other value"  # Prints "You're nailing this readme!"
```

#### Argument 2
Type: `Number|Boolean`  
Default: 100

Copy-paste as many of these as you need.

## Contributing

When you publish something open source, one of the greatest motivations is that
anyone can just jump in and start contributing to your project.

These paragraphs are meant to welcome those kind souls to feel that they are
needed. You should state something like:

"If you'd like to contribute, please fork the repository and use a feature
branch. Pull requests are warmly welcome."

If there's anything else the developer needs to know (e.g. the code style
guide), you should link it here. If there's a lot of things to take into
consideration, it is common to separate this section to its own file called
`CONTRIBUTING.md` (or similar). If so, you should say that it exists here.

## Links

Even though this information can be found inside the project on machine-readable
format like in a .json file, it's good to include a summary of most useful
links to humans using your project. You can include links like:

- Project homepage: https://your.github.com/awesome-project/
- Repository: https://github.com/your/awesome-project/
- Issue tracker: https://github.com/your/awesome-project/issues
  - In case of sensitive bugs like security vulnerabilities, please contact
    my@email.com directly instead of using issue tracker. We value your effort
    to improve the security and privacy of this project!
- Related projects:
  - Your other project: https://github.com/your/other-project/
  - Someone else's project: https://github.com/someones/awesome-project/


## Licensing

"The code in this project is licensed under MIT license."


==============================

# multicast-checker
To check the IPTV channels streams (UDP based)

# multicast-scanner
The script will scan the UDP IPs range for the given ports (default '1234').
As a result the resulting m3u file will be created.

If the --playlst parameter with the existing m3u file is defined the script will use all the unique ports from it
Additional UDP ports can be defined via --port argument(s). Example below:
--port 5500 5555
Please read the manual (run the script with -h parameter) for more info

Data used:
- https://www.iana.org/assignments/multicast-addresses/multicast-addresses.xhtml
- https://www.davidc.net/sites/default/subnets/subnets.html