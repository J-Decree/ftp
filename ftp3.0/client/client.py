from socket import *
import json
import struct

IP_PORT = ('localhost', 8888)

AUTH_USER_NOT_EXIST = 501
AUTH_PASSWORD_NOT_CORRECT = 502
AUTH_USER_HAS_LOGIN = 503
AUTH_SUCCESS = 500


class ClientHandler(object):
    def __init__(self):
        self.sock = socket()
        self.sock.connect(IP_PORT)

    def interactive(self):
        if self.auth():
            while True:
                ch = input('>> ').strip()
                self.sock.send(ch.encode('utf8'))

    def auth(self):
        username = input("请输入用户名： ")
        password = input('请输入密码: ')
        d = {'action': 'auth', 'username': username, 'password': password}
        self.sock.send(json.dumps(d).encode('utf8'))

        data = self.sock.recv(4)
        print(data)
        status = struct.unpack('i', data)[0]
        print(status)
        if status == AUTH_USER_NOT_EXIST:
            print('用户名不存在')
        elif status == AUTH_USER_HAS_LOGIN:
            print('用户名已经登录')
        elif status == AUTH_PASSWORD_NOT_CORRECT:
            print('密码不正确')
        elif status == AUTH_SUCCESS:
            print('认证成功')
            return True
        else:
            print('出错')


if __name__ == '__main__':
    c = ClientHandler()
    c.interactive()
