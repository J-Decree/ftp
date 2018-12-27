import os
import socketserver
import struct
import json
import configparser
import shutil
import sys
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from conf.setting import *
from lib.ProgressBar import ProgressBar


class ServerHandler(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            # {'action':'auth','username':'ziyi','password':'123'}
            self.interactive()

    def interactive(self):
        data = self.request.recv(1024)
        data = data.decode('utf8')
        if data:
            d = json.loads(data)
            if 'action' in d:
                if hasattr(self, d['action']):
                    func = getattr(self, d['action'])
                    func(**d)

    def auth(self, **d):
        username = d.get('username')
        password = d.get('password')
        return self.authenicate(username, password)

    def authenicate(self, username, password):
        user_db = os.path.join(BASE_DIR, 'db', 'user.cfg')
        config = configparser.ConfigParser()
        config.read(user_db)
        if username in config.sections():
            if config.get(username, 'password') == password:
                self.__send_status(AUTH_SUCCESS)
                self.__init_home(username)
                print('认证成功')
            else:
                self.__send_status(AUTH_PASSWORD_NO_CORRECT)
                print('密码错误')
        else:
            self.__send_status(AUTH_USER_NO_EXIST)
            print('用户不存在')

    def __send_status(self, status):
        data = struct.pack('b', status)
        self.request.send(data)
        if status in [AUTH_PASSWORD_NO_CORRECT, AUTH_USER_NO_EXIST]:
            self.finish()

    def __init_home(self, username):
        self.username = username
        self.home_path = os.path.join(BASE_DIR, 'home', username)
        self.now_path = self.home_path
        self.pre_path = self.home_path
        self.home_maxsize = HOME_MAX_SIZE
        if not os.path.exists(self.home_path):
            os.makedirs(self.home_path)

    def upload(self, **kwargs):
        # 获得客户端要上传的文件信息
        file_name = kwargs.get('file_name')
        file_size = kwargs.get('file_size')
        target_path = kwargs.get('target_path')

        # 判断是否超出指定配额
        if file_size > self.home_maxsize:
            self.__send_status(UPLOAD_OVER_HOME_SIZE)
            return
        self.home_maxsize -= file_size

        if '/' in target_path:
            # 指定了目标路径
            path_list = target_path.split('/')
            # isdir/a/
            # isdir/a/ccc.pdf
            abs_dir = self.__get_target_abspath(path_list[:-1], self.now_path)
            if not abs_dir:
                self.__send_status(UPLOAD_TARGET_PATH_ERROR)
                return
            if target_path.endswith('/'):
                abs_path = os.path.join(abs_dir, file_name)
            else:
                abs_path = os.path.join(abs_dir, path_list[-1])
        else:
            # 没有指定目标路径
            abs_path = os.path.join(self.now_path, file_name)

        if os.path.exists(abs_path):
            self.__send_status(UPLOAD_FILE_TRUNCATE)
            data = self.request.recv(1024)
            ch = data.decode('utf8')
            if ch == 'Y':
                now_size = os.path.getsize(abs_path)
                self.request.send(str(now_size).encode('utf8'))
                smd5 = self.__upload_truncate_recv(abs_path, file_size, now_size)
                self.request.send(smd5.encode('utf8'))
            else:
                smd5 = self.__upload_normal_recv(abs_path, file_size)
                self.request.send(smd5.encode('utf8'))
        else:
            self.__send_status(UPLOAD_READY)
            smd5 = self.__upload_normal_recv(abs_path, file_size)
            self.request.send(smd5.encode('utf8'))

    def __upload_truncate_recv(self, abs_path, file_size, now_size):
        m = hashlib.md5()
        file_size -= now_size
        has_recv = 0
        f = open(abs_path, 'ab')
        p = ProgressBar(file_size)
        while file_size > has_recv:
            data = self.request.recv(1024)
            f.write(data)
            m.update(data)
            has_recv += len(data)
            p.show_progress(has_recv)
        f.close()
        return m.hexdigest()

    def __upload_normal_recv(self, abs_path, file_size):
        m = hashlib.md5()
        has_recv = 0
        f = open(abs_path, 'wb+')
        p = ProgressBar(file_size)
        while file_size > has_recv:
            data = self.request.recv(1024)
            f.write(data)
            m.update(data)
            has_recv += len(data)
            p.show_progress(has_recv)
        f.close()
        return m.hexdigest()

    def ls(self, **kwargs):
        file_list = os.listdir(self.now_path)
        file_str = '\t'.join(file_list)
        if not file_str:
            file_str = ' '
        self.request.send(file_str.encode('utf8'))

    def cd(self, **kwargs):
        target_dir = kwargs.get('target_dir')
        home = os.path.join(BASE_DIR, 'home')

        if not target_dir:
            # cd
            self.request.send(self.home_path[len(home) + 1:].encode('utf8'))
            self.now_path = self.home_path
        else:
            # 存在目标路径
            if target_dir == '..':
                # cd ..
                if self.now_path == self.home_path:
                    self.request.send(self.now_path[len(home) + 1:].encode('utf8'))
                else:
                    self.pre_path = self.now_path
                    self.now_path = os.path.dirname(self.now_path)
                    self.request.send(self.now_path[len(home) + 1:].encode('utf8'))
            elif target_dir == '-':
                # cd -
                self.pre_path, self.now_path = self.now_path, self.pre_path
                self.request.send(self.now_path[len(home) + 1:].encode('utf8'))
            else:
                # 处理路径
                if '/' not in target_dir:
                    # 处理相对路径
                    target_dir = os.path.join(self.now_path, target_dir)
                    if not os.path.exists(target_dir):
                        self.request.send('文件夹不存在'.encode('utf8'))
                    else:
                        self.request.send(target_dir[len(home) + 1:].encode('utf8'))
                        self.now_path, self.pre_path = target_dir, self.now_path
                else:
                    # 处理绝对路径
                    target_dir_list = target_dir.split('/')
                    abs_target_dir = self.__get_target_abspath(target_dir_list, self.now_path)
                    if not abs_target_dir:
                        self.request.send('文件夹不存在'.encode('utf8'))
                    else:
                        self.request.send(abs_target_dir[len(home) + 1:].encode('utf8'))
                        self.now_path, self.pre_path = abs_target_dir, self.now_path

    def mkdir(self, **kwargs):
        target_dir = kwargs.get('target_dir')
        if target_dir in os.listdir(self.now_path):
            self.request.send('文件夹已存在'.encode('utf8'))
            return
        target_dir = os.path.join(self.now_path, target_dir)
        if '/' in target_dir:
            os.makedirs(target_dir)
        else:
            os.mkdir(target_dir)

        self.request.send('成功创建文件夹'.encode('utf8'))

    def pwd(self, **kwargs):
        home = os.path.join(BASE_DIR, 'home')
        self.request.send(self.now_path[len(home) + 1:].encode('utf8'))

    def rm(self, **kwargs):
        is_rf = kwargs.get('rf')
        target = kwargs.get('target')

        target = os.path.join(self.now_path, target)
        if not os.path.exists(target):
            self.request.send('文件不存在'.encode('utf8'))
            return

        if is_rf:
            # 删除任意
            if os.path.isdir(target):
                shutil.rmtree(target)
                self.request.send('删除文件夹成功'.encode('utf8'))
            elif os.path.isfile(target):
                os.remove(target)
                self.request.send('删除文件成功'.encode('utf8'))
        else:
            # 不能删除文件夹
            if os.path.isdir(target):
                self.request.send('该命令不能删除文件夹'.encode('utf8'))
            elif os.path.isfile(target):
                os.remove(target)
                self.request.send('删除文件成功'.encode('utf8'))

    def __get_target_abspath(self, path_list, res_path, now_index=0):
        # ~/apple/bear/love
        # isdir/love/a
        if len(path_list) == now_index:
            return res_path
        if path_list[now_index] == '~':
            if now_index == 0:
                res_path = self.home_path
                return self.__get_target_abspath(path_list, res_path, now_index + 1)
            else:
                return

        else:
            if path_list[now_index] in os.listdir(res_path):
                res_path = os.path.join(res_path, path_list[now_index])
                return self.__get_target_abspath(path_list, res_path, now_index + 1)
            else:
                return


if __name__ == '__main__':
    pass
