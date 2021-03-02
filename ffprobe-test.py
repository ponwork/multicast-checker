import os
import json


address = '233.99.65.1'
port = 1234

def get_ffmpeg_sample(address, port, lenght=10):
    """ To get the stream sample """
    os.system(f'ffmpeg -y -v quiet -i udp://@{address}:{port} -vcodec copy -acodec copy -t {lenght} sample_{address}-{port}.mp4')
    print(f'[*] Sample for {address}:{port} captured')

def get_ffprobe(address, port):
    """ To get the json data from ip:port """

    stdout = os.popen(f'ffprobe -v quiet -print_format json -show_programs udp://{address}:{port}')
    data = stdout.read()
    json_string = json.loads(str(data))
    for item in json_string['programs']:
        service_name = item['tags']['service_name']
        if service_name == '':
            print('[*] No service_name')
            get_ffmpeg_sample(address, port)
        else:
            print(service_name)

get_ffprobe(address, port)