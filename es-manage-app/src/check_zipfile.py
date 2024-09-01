import os
import pprint
import zipfile
from zipfile import ZipFile
import traceback

import zlib
import sys
import hashlib


def get_hash(file_path):
    f = open(file_path, 'rb')
    data = f.read()
    f.close()    
    return {'crc':hex(zlib.crc32(data))[2:], 'md5':hashlib.md5(data).hexdigest(), 'sha1':hashlib.sha1(data).hexdigest()}

file_path = r'd:\Double Dragon (USA).zip'
if file_path[-4:] == '.zip':
    archive = ZipFile(file_path, 'r')
    for file_info in archive.infolist():
        file_name = file_info.filename
        file_size = file_info.file_size
        print(file_name, file_size)
        with archive.open(file_name, 'r') as fp:
            data = fp.read()
        print({'crc':hex(zlib.crc32(data))[2:], 'md5':hashlib.md5(data).hexdigest(), 'sha1':hashlib.sha1(data).hexdigest()})
    
else:
    print(get_hash(file_path))