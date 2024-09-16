from ppadb.client import Client as AdbClient
from main_new import MatchingRoms
import os,sys
import time


import subprocess

import paramiko

def get_file_list(host, port, username, password, remote_path):
    try:
        # SSH 클라이언트 생성
        client = paramiko.SSHClient()
        
        # 호스트 키 자동 추가
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # SSH 연결
        client.connect(hostname=host, port=port, username=username, password=password, timeout=5)
        print(f"Connected to {host}")

        # 원격 명령 실행 - 특정 경로의 파일 목록 가져오기
        command = f"ls {remote_path}"
        stdin, stdout, stderr = client.exec_command(command)

        # 명령 실행 결과 출력
        output = stdout.read().decode().splitlines()  # 결과를 줄 단위로 나누어 리스트로 변환
        error = stderr.read().decode()

        if error:
            print(f"Error:\n{error}")
            return []

        # SSH 연결 종료
        client.close()

        # 파일 목록 반환
        return output

    except Exception as e:
        print(f"An error occurred: {e}")



class ADBConnection:

    def __init__(self) -> None:
        ori_path = os.getcwd()
        if getattr(sys,'frozen',False):
            self.program_directory = os.path.dirname(os.path.abspath(sys.executable))  
        else:  
            self.program_directory = os.path.dirname(os.path.abspath(__file__))
        # os.chdir(program_directory)
        subprocess.run([self.program_directory+'\\'+r'adb\adb', 'start-server'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def connect(self):
        # # Default is "127.0.0.1" and 5037
        client = AdbClient(host="127.0.0.1", port=5037)

        while True:
            devices = client.devices()
            if len(devices) == 0:
                time.sleep(1)
                continue

            try:
                device_name = devices[0].shell('getprop ro.product.model').strip()
                serial = devices[0].serial
                return (device_name, serial)
            except:
                # print('wait')
                time.sleep(1)
                continue
    def disconnect(self):
        subprocess.run([self.program_directory+'\\'+r'adb\adb', 'kill-server'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)




    def get_android_directory_list(self, directory="/storage/emulated/0/"):
        try:
            # ADB 명령어 실행하여 디렉토리 목록 가져오기
            result = subprocess.run([self.program_directory+'\\'+r'adb\adb', 'shell', 'ls', directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # 오류 발생 시
            if result.returncode != 0:
                print(f"Error: {result.stderr}")
                return None
            
            # 결과 출력
            return result.stdout.splitlines()

        except Exception as e:
            print(f"An error occurred: {e}")
            return None

# 내부 저장소의 파일 및 폴더 목록 확

# adb_conn = ADBConnection()
# directory_list = adb_conn.get_android_directory_list("/storage/emulated/0/ROMs/vita")
# if directory_list:
#     print("Directory List:")
#     for item in directory_list:
#         print(item)


# SSH 연결 정보
host = "192.168.50.140"
port = 22  # 기본 SSH 포트
username = "ark"
password = "ark"
remote_path = "/roms2/snes"  # 원격 경로

# 특정 경로의 파일 목록 가져오기
for i in get_file_list(host, port, username, password, remote_path):
    print(i)

