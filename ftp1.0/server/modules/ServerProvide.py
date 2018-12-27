#!/usr/bin/env python
# coding=utf-8
import socketserver
import json
import configparser
import os
import struct
import subprocess
from conf.setting import *
from modules import ProcessBar

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ServerProvide(socketserver.BaseRequestHandler):
    def handle(self):
        if self.auth():
            # self.init_home()
            while True:
                self.interactive()

    def interactive(self):
        # 命令分发
        data = self.request.recv(1024)
        data = data.decode('utf8')
        datas = data.split()
        cmd = datas[0]

        # TODO 调试代码
        print('datas:', datas)
        print(cmd)

        if hasattr(self, cmd):
            func = getattr(self, cmd)
            func(self, datas[1:])
        else:
            self.__send_status(CMD_NOT_EXIST)

    def cd(self, *args):
        print(args)

    def download(self, *args):
        print(args, 'download')
        filename = args[1][0]
        data = self.request.recv(1024)
        data = data.decode("utf8")
        d = json.loads(data)
        filesize = d['filesize']
        if filename not in os.listdir():
            self.__send_status(DOWNLOAD_FILE_NOT_EXIST)
            return
        else:
            if filesize != 0:
                # 断点续传
                self.__send_status(DOWNLOAD_FILE_TRUNCATE)
                size = os.path.getsize(filename)
                l = struct.pack('i', size)
                self.request.sendall(l)
                f = open(filename, 'rb')
                f.seek(filesize)
                size -= filesize
                p = ProcessBar.ProcessBar(size)
                now_size = 0
                while size > now_size:
                    self.request.sendall(f.read(1024))
                    now_size += 1024
                    p.show_process(now_size)
                f.close()

            else:
                self.__send_status(DOWNLOAD_READY)
                size = os.path.getsize(filename)
                l = struct.pack('i', size)
                self.request.sendall(l)
                f = open(filename, 'rb')
                p = ProcessBar.ProcessBar(size)
                now_size = 0
                while size > now_size:
                    self.request.sendall(f.read(1024))
                    now_size += 1024
                    p.show_process(now_size)
                f.close()

    def upload(self, *args):
        print(args, 'upload')
        filename = args[1][0]
        data = self.request.recv(1024)
        data = data.decode("utf8")
        d = json.loads(data)

        filesize = d['filesize']
        if self.home_size < filesize:
            self.__send_status(UPLOAD_OVER_HOME_SIZE)
            return

        self.home_size -= filesize
        if filename in os.listdir():
            # 断点上传
            self.__send_status(UPLOAD_FILE_TRUNCATE)
            size = os.path.getsize(filename)
            s = struct.pack('i', size)
            self.request.sendall(s)
            f = open(filename, 'ab')
            filesize -= size
            p = ProcessBar.ProcessBar(filesize)
            now_size = 0
            while filesize > now_size:
                data = self.request.recv(1024)
                f.write(data)
                now_size += len(data)
                p.show_process(now_size)
            f.close()
        else:
            self.__send_status(UPLOAD_READY)
            f = open(filename, 'wb')
            p = ProcessBar.ProcessBar(filesize)
            now_size = 0
            while filesize > now_size:
                data = self.request.recv(1024)
                f.write(data)
                now_size += len(data)
                p.show_process(now_size)
            f.close()

    def ls(self, *args):
        if len(args[1]) > 1:
            self.__send_status(CMD_NOT_EXIST)
            return
        s = subprocess.Popen('ls', shell=True, stdout=subprocess.PIPE)
        self.__send_status(CMD_SUCCESS)
        sdata = s.stdout.read()
        if sdata == b'':
            sdata = b' '
        self.request.sendall(sdata)

    def auth(self):
        data = self.request.recv(1024)
        data = data.decode('utf8')
        d = json.loads(data)
        c = configparser.ConfigParser()
        user_db = os.path.join(BASE_DIR, 'db', 'user.cfg')
        c.read(user_db)
        if c.has_section(d['username']):
            if c.get(d['username'], 'password') == d['password']:
                self.__send_status(NORMAL_STATUS)
                print('验证成功')
                self.username = d['username']
                self.home_size = HOME_MAX_SIZE
                self.home_dir = os.path.join(BASE_DIR, d['username'])
                return True
            else:
                self.__send_status(AUTH_PASSWORD_NO_CORRECT)
                print('密码不对')
        else:
            self.__send_status(AUTH_USER_NO_EXIST)
            print('不存在用户名')

    def init_home(self):
        if not os.path.exists(self.home_dir):
            os.mkdir(self.home_dir)
        os.chdir(self.home_dir)

    def __send_status(self, status):
        data = struct.pack('b', status)
        self.request.sendall(data)
        if status in [AUTH_PASSWORD_NO_CORRECT, AUTH_USER_NO_EXIST]:
            self.finish()
