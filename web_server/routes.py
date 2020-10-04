from . import app
import os
import globalconfig
import re
from flask import request, Response, render_template, stream_with_context

full_path = "/home/gokul/Downloads/Telegram Desktop/Movies/Tai Chi Hero " \
            "2012/Tai.Chi.Hero.2012.BluRay.720p.x264.Ganool.mkv"
file_size = os.stat(full_path).st_size
DEBUG = True


def print_d(line):
    if DEBUG:
        print(line)


def get_file_system(path):
    if os.path.isfile(path):
        return
    dir_list = os.listdir(path)
    file_system_structure = {}
    if not len(dir_list):
        return file_system_structure

    files = []

    for directory in dir_list:
        if os.path.isdir(os.path.join(path, directory)):
            file_system_structure[directory] = get_file_system(os.path.join(path, directory))
        if os.path.isfile(os.path.join(path, directory)):
            files.append(directory)

    if files:
        file_system_structure['files'] = files
    return file_system_structure


@app.after_request
def after_request(response):
    response.headers.add('Accept-Ranges', 'bytes')
    return response


@app.route('/video')
def get_video_file():
    global file_size
    print(f"Request made... File size : {file_size}")
    range_header = request.headers.get('Range', None)
    file_params = {
        'length': globalconfig.two_mb,
        'start': 0
    }

    start_byte, end_byte = 0, None
    if range_header:
        match = re.search(r'(\d+)-(\d*)', range_header)
        groups = match.groups()
        if groups[0]:
            start_byte = int(groups[0])
        if groups[1]:
            end_byte = int(groups[1])

        if start_byte < file_size:
            file_params['start'] = start_byte
        if end_byte:
            file_params['length'] = end_byte + 1 - start_byte
        if start_byte + globalconfig.two_mb > file_size:
            file_params['length'] = file_size - file_params['start']

        print_d(f'Start Byte : {start_byte}, End Byte : {end_byte}')

    def generator():
        with open(full_path, 'rb') as fd:
            while file_params['start'] < file_size:
                fd.seek(file_params['start'])
                chunk_g = fd.read(file_params['length'])
                if file_params['start'] + file_params['length'] >= file_size:
                    file_params['length'] = file_size - file_params['start']
                print_d(f"Yield chuck, Start : {file_params['start']} Length : {file_params['length']}")
                file_params['start'] = min(file_params['start'] + file_params['length'], file_size)
                yield chunk_g

            print_d(f"Exit from generator...Start : {file_params['start']}  File Size : {file_size}")
    if file_params['length'] == globalconfig.two_mb:
        response = Response(stream_with_context(generator()), 206, mimetype='video/mp4', content_type='video/mp4',
                            direct_passthrough=True)
    else:
        with open(full_path, 'rb') as f:
            f.seek(file_params['start'])
            chunk = f.read(file_params['length'])
        response = Response(chunk, 206, mimetype='video/mp4', content_type='video/mp4',
                            direct_passthrough=True)
    response.headers.add('Content-Range',
                         f"bytes {file_params['start']}-{file_params['start'] + file_params['length'] - 1}/{file_size}")
    print_d(f"Start : {file_params['start']}, Length : {file_params['length']}")
    return response


@app.route('/play')
def play_content():
    return render_template('play_page.html')
