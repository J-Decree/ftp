from socket import *
import json
import struct
import os

IP_PORT = ('localhost', 8888)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class ClientHandler(object):
    def __init__(self):
        self.sock = socket()
        self.make_connect()

    def make_connect(self):
        self.sock.connect(IP_PORT)

    def interactive(self):
        while True:
            ch = input('>> ')
            info = ch.split()
            action = info[0]
            print('info: ', info)
            print('action: ', action)
            if hasattr(self, action):
                func = getattr(self, action)
                func(*info)
            else:
                self.talk(*info)

    def download(self, *args):
        if len(args) != 2:
            print('格式错误')
            return
        file_name = args[1]
        action_dict = {'action': 'download', 'filename': file_name}
        self.sock.send(json.dumps(action_dict).encode('utf8'))
        data = self.sock.recv(1)
        status = struct.unpack('b', data)[0]
        if status == 100:
            data = self.sock.recv(4)
            file_size = struct.unpack('i', data)[0]
            f = open(file_name, 'wb')
            now_size = 0
            print(file_size)
            while file_size > now_size:
                data = self.sock.recv(1024)
                f.write(data)
                now_size += len(data)
                print('接收了%d字节\r' % len(data))
            f.close()
            print('下载完毕了')
        else:
            print('not exist this file')

    def upload(self, *args):
        if len(args) != 2:
            print('格式错误')
            return

        file_name = args[1]
        file_path = os.path.join(BASE_DIR, file_name)
        if not os.path.exists(file_path):
            print('不存在的文件')
            return
        file_size = os.path.getsize(file_path)
        action_dict = {'action': 'upload', 'filename': file_name, 'filesize': file_size}

        self.sock.send(json.dumps(action_dict).encode('utf8'))

        f = open(file_path, 'rb')
        now_size = 0
        while file_size > now_size:
            data = f.read(100)
            self.sock.send(data)
            now_size += len(data)
            print('发送了%s字节\r' % now_size)
        f.close()
        print('文件上传完毕')

    def talk(self, *info):

        self.sock.send(''.join(info).encode('utf8'))


if __name__ == '__main__':
    c = ClientHandler()
    c.interactive()
