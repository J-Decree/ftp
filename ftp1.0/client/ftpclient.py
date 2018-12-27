from socket import *
import re
import optparse
import json
import struct
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from conf.setting import *
from modules import PrcocessBar


class ClientHandler(object):
    def __init__(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        ip_port = self.verify_args()
        self.make_connect(ip_port)
        if self.auth():
            self.interactive()

    def make_connect(self, ip_port):
        if ip_port:
            print('尝试链接')
            self.sock.connect(ip_port)
        else:
            print('尝试链接默认127.0.0.1 8888')
            print(IP_PORT)
            self.sock.connect(IP_PORT)

    def verify_args(self):
        op = optparse.OptionParser()
        op.add_option('-s', '--server', dest='server')
        op.add_option('-p', '--port', dest='port')
        options, args = op.parse_args()
        if not all([options.port, options.server]):
            return
        m = re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', options.server)
        if not m:
            print('ip地址格式错误')
            return
        m = re.match(r'^\d{1,5}$', options.port)
        if not m:
            print('端口设置错误')
            return

        port = int(options.port)
        ip = m.group()
        return ip, port

    def help(self):
        print('Format not correct!')
        print('You must check your version of Python')
        print('Example: python ftpclient.py -s 127.0.0.1 -p 8888')

    def auth(self):
        username = input('请输入账号: ')
        password = input('请输入密码： ')
        d = {'username': username, 'password': password}
        self.sock.send((json.dumps(d)).encode('utf8'))
        data = self.sock.recv(1)
        status = struct.unpack('b', data)[0]
        if status == AUTH_USER_NO_EXIST:
            print(STATUS_TIPS[status])
            return
        elif status == AUTH_PASSWORD_NO_CORRECT:
            print(STATUS_TIPS[status])
            return

        self.home_path = 'ftp-server :%s' % d['username'] + ' $ '
        return True

    def interactive(self):
        while True:
            data = input(self.home_path).strip()
            # 判断是不是上传文件请求
            if data.startswith('upload '):
                upload_file = data[len('upload '):]
                self.upload(upload_file)

            # 判断是不是下载文件请求
            elif data.startswith('download '):
                download_file = data[len('download '):]
                self.download(download_file)
            else:
                self.sock.send(data.encode('utf8'))

            # 开始接收数据
            data = self.sock.recv(1)
            header_status = struct.unpack('b', data)[0]
            if header_status == CMD_SUCCESS:
                # 显示cmd执行命令结果
                print(STATUS_TIPS[CMD_SUCCESS])
                data = self.sock.recv(1024)
                print(data.decode('utf8'))
            elif header_status == CMD_CD:
                # cd的更新家目录
                pass
            elif header_status == CMD_NOT_EXIST:
                print(STATUS_TIPS[CMD_NOT_EXIST])

    def upload(self, filename):
        filepath = os.path.abspath(filename)
        print(filepath)
        if not os.path.exists(filepath):
            print('host have not this file')
            self.sock.send(b'dd')
            return
        self.sock.send(('upload %s' % filename).encode('utf8'))
        filesize = os.path.getsize(filepath)
        d = {'filesize': filesize}
        self.sock.send(json.dumps(d).encode('utf8'))
        data = self.sock.recv(1)
        status = struct.unpack('b', data)[0]
        print(status)
        if status == UPLOAD_OVER_HOME_SIZE:
            print(STATUS_TIPS[status])
        elif status == UPLOAD_READY:
            print('准被上传')
            f = open(filepath, 'rb')
            p = PrcocessBar.ProcessBar(filesize)
            now_size = 0
            while filesize > now_size:
                self.sock.send(f.read(1024))
                now_size += 1024
                p.show_process(now_size)
            f.close()
        elif status == UPLOAD_FILE_TRUNCATE:
            print('准备断点上传')
            data = self.sock.recv(4)
            l = struct.unpack('i', data)[0]
            f = open(filepath, 'rb')
            f.seek(l)
            filesize -= l
            p = PrcocessBar.ProcessBar(filesize)
            now_size = 0
            while filesize > now_size:
                self.sock.send(f.read(1024))
                now_size += 1024
                p.show_process(now_size)
            f.close()

    def download(self, filename):
        self.sock.send(('download %s' % filename).encode('utf8'))
        if os.path.exists(filename):
            filesize = os.path.getsize(filename)
            d = {'filesize': filesize}
            data = self.sock.recv(1)
            status = struct.unpack('b', data)[0]
            if status == DOWNLOAD_FILE_NOT_EXIST:
                print(STATUS_TIPS[status])
            elif status == DOWNLOAD_FILE_TRUNCATE:
                data = self.sock.recv(4)
                size = struct.unpack('i', data)[0]
                size -= filesize
                f = open(filename, 'rb')
                f.seek(filesize)
                p = PrcocessBar.ProcessBar(size)
                now_size = 0
                while size > now_size:
                    data = self.sock.recv(1024)
                    f.write(data)
                    now_size += 1024
                    p.show_process(now_size)
                f.close()
        else:
            d = {'filesize': 0}
            self.sock.send(json.dumps(d).encode('utf8'))
            data = self.sock.recv(1)
            status = struct.unpack('b', data)[0]
            if status == DOWNLOAD_FILE_NOT_EXIST:
                print(STATUS_TIPS[status])
            elif status == DOWNLOAD_READY:
                data = self.sock.recv(4)
                size = struct.unpack('i', data)[0]
                f = open(filename, 'rb')
                p = PrcocessBar.ProcessBar(size)
                now_size = 0
                while size > now_size:
                    data = self.sock.recv(1024)
                    f.write(data)
                    now_size += 1024
                    p.show_process(now_size)
                f.close()

    def __send_status(self, status):
        data = struct.pack('b', status)
        self.sock.sendall(data)


if __name__ == '__main__':
    ClientHandler()
