import optparse
import os
import sys
import json
import struct
import hashlib
from socket import *
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from conf.setting import *
from lib.ProgressBar import ProgressBar


class ClientHandler(object):
    def __init__(self):
        ip_port = self.verify_args()
        self.make_connection(ip_port)

    def verify_args(self):
        op = optparse.OptionParser()
        op.add_option('-s', '--server', dest='server')
        op.add_option('-p', '--port', dest='port')
        options, args = op.parse_args()
        if not all([options.server, options.port]):
            return IP_PORT
        return options.server, int(options.port)

    def make_connection(self, ip_port):
        self.sock = socket()
        self.sock.connect(ip_port)

    def auth(self):
        username = input('请输入用户名: ').strip()
        password = input('请输入密码: ').strip()
        d = {'action': 'auth', 'username': username, 'password': password}
        self.sock.send(json.dumps(d).encode('utf8'))
        res = self.get_auth_result()
        if res:
            self.__init_server_home(username)
        return res

    def get_auth_result(self):
        data = self.sock.recv(1)
        status = struct.unpack('b', data)[0]
        if status == AUTH_SUCCESS:
            print('认证成功')
            return True
        print(STATUS_TIPS[status])

    def __init_server_home(self, username):
        self.username = username
        self.now_path = os.path.join(username)

    def interactive(self):
        if self.auth():
            print('开始交互..')
            while True:
                cmd_info = input('%s:%s$ ' % (self.username, self.now_path[len(self.username) + 1:])).strip()
                if cmd_info:
                    cmd_list = cmd_info.split()
                    if hasattr(self, cmd_list[0]):
                        func = getattr(self, cmd_list[0])
                        func(*cmd_list)
                    else:
                        print(STATUS_TIPS[CMD_NOT_EXIST])

    def download(self, *args):
        print(args)
        for i in args:
            print(i)

    def upload(self, *args):
        # 输入的命令参数判断
        if len(args) == 2:
            action, local_path = args
            target_path = ''
        elif len(args) == 3:
            action, local_path, target_path = args
        else:
            print('Example: upload target_file [target_path]')
            return

        # 文件路径判断，若不存在直接返回
        mydir = os.getcwd()
        local_path = os.path.join(mydir, local_path)
        if not os.path.exists(local_path):
            print('文件不存在')
            return

        # 文件信息处理
        file_name = os.path.basename(local_path)
        file_size = os.path.getsize(local_path)

        file_info = {
            'action': 'upload',
            'file_name': file_name,
            'file_size': file_size,
            'target_path': target_path,
        }

        # 文件信息发送
        self.sock.send(json.dumps(file_info).encode('utf8'))

        # 获得处理结果
        self.get_upload_result(**file_info)

    def get_upload_result(self, **file_info):
        data = self.sock.recv(1)
        file_status = struct.unpack('b', data)[0]
        file_name = file_info['file_name']
        file_size = file_info['file_size']

        if file_status == UPLOAD_OVER_HOME_SIZE:
            print('容量不够')
        elif file_status == UPLOAD_READY:
            md5 = self.__normal_upload_file(file_name, file_size)
            self.__chekc_md5(md5)
        elif file_status == UPLOAD_FILE_TRUNCATE:
            ch = input('文件已经有了，断点传续Y,重传任意键').strip()
            self.sock.send(ch.upper().encode('utf8'))
            if ch.upper() == 'Y':
                data = self.sock.recv(1024)
                now_size = int(data.decode('utf8'))
                md5 = self.__truncate_upload_file(file_name, file_size, now_size)
                self.__chekc_md5(md5)
            else:
                md5 = self.__normal_upload_file(file_name, file_size)
                self.__chekc_md5(md5)
        elif file_status == UPLOAD_TARGET_PATH_ERROR:
            print('目标路径设置错误')

    def __chekc_md5(self, md5):
        data = self.sock.recv(1024)
        smd5 = data.decode('utf8')
        print(smd5)
        print(md5)
        if md5 == smd5:
            print('文件一致性验证通过，上传成功')
            return True
        else:
            print('文件一致性未通过，上传未成功')

    def __normal_upload_file(self, file_name, file_size):
        print('已经准备好了，现在为你上传')
        has_send = 0
        p = ProgressBar(file_size)
        m = hashlib.md5()

        f = open(file_name, 'rb')
        while file_size > has_send:
            data = f.read(1024)
            m.update(data)
            self.sock.send(data)
            has_send += 1024
            p.show_progress(has_send)
        f.close()
        print(m.hexdigest())
        print(type(m.hexdigest()))
        return m.hexdigest()

    def __truncate_upload_file(self, file_name, file_size, now_size):
        f = open(file_name, 'rb')
        f.seek(now_size)
        file_size -= now_size
        has_send = 0
        p = ProgressBar(file_size)
        m = hashlib.md5()
        while file_size > has_send:
            data = f.read(1024)
            m.update(data)
            self.sock.send(data)
            has_send += 1024
            p.show_progress(has_send)
        f.close()
        return m.hexdigest()

    def ls(self, *args):
        if len(args) > 1:
            print('Example: ls')
            return
        cmd_info = {'action': 'ls'}
        self.sock.send(json.dumps(cmd_info).encode('utf8'))
        data = self.sock.recv(1024)
        print(data.decode('utf8'))

    def cd(self, *args):
        # 输入参数处理
        if len(args) > 2:
            print('Example: cd  example_dir')
            return

        # 协议头处理
        if len(args) == 1:
            cmd_info = {'action': 'cd'}
        else:
            cmd_info = {'action': 'cd', 'target_dir': args[1]}

        # 发送协议头
        self.sock.send(json.dumps(cmd_info).encode('utf8'))

        # 处理服务器返回的结果
        data = self.sock.recv(1024)
        print(data.decode('utf8'))
        self.now_path = data.decode('utf8')

    def mkdir(self, *args):
        # 参数判断
        if len(args) > 2 or len(args) == 1:
            print('example:mkdir xxdir')
            return
        # 协议头处理
        cmd_info = {'action': 'mkdir', 'target_dir': args[1]}

        # 发送协议头
        self.sock.send(json.dumps(cmd_info).encode('utf8'))

        # 处理返回结果
        data = self.sock.recv(1024)
        print(data.decode('utf8'))

    def pwd(self, *args):
        if len(args) > 1:
            print('example:pwd')
            return
        cmd_info = {'action': 'pwd'}
        self.sock.send(json.dumps(cmd_info).encode('utf8'))
        data = self.sock.recv(1024)
        print(data.decode('utf8'))

    def rm(self, *args):
        if len(args) == 2:
            cmd_info = {'action': 'rm', 'rf': False, 'target': args[1]}
        elif len(args) == 3 and args[1] == '-rf':
            cmd_info = {'action': 'rm', 'rf': True, 'target': args[2]}
        else:
            print('example1: rm xx.py')
            print('example2: rm -rf xxdir')
            return
        self.sock.send(json.dumps(cmd_info).encode('utf8'))
        data = self.sock.recv(1024)
        print(data.decode('utf8'))

    def lls(self, *args):
        # local ls
        # local ls 和 local cd 就不作记录了，直接操纵工作目录
        if len(args) > 1:
            print('example: lls')
            return
        print('\t'.join(os.listdir()))

    def lcd(self, *args):
        # local cd
        if len(args) > 2:
            print('example1: cd ')
            print('example2: cd ..')
            print('example3: cd path')
        target_path = args[1]
        try:
            os.chdir(target_path)
        except:
            print('没有该文件夹')

    def lpwd(self, *args):
        if len(args) > 1:
            print('example: lpwd')
            return
        print(os.getcwd())


if __name__ == '__main__':
    c = ClientHandler()
    c.interactive()
