import zlib
import sys
import hashlib


def get_hash(file_path):
    f = open(file_path, 'rb')
    data = f.read()
    f.close()    
    return {'crc':hex(zlib.crc32(data))[2:], 'md5':hashlib.md5(data).hexdigest(), 'sha1':hashlib.sha1(data).hexdigest()}


if __name__ == '__main__':
    file_path = r'd:\Double Dragon (USA).nes'
    print(get_hash(file_path))