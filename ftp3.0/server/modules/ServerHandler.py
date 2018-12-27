from socket import *
from conf.setting import *
import configparser
import json
import selectors
import struct


class ServerHandler(object):
    def __init__(self):
        self.sock = socket()
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind(IP_PORT)
        self.sock.listen(10)
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept)
        self.online_dict = {}

    def run(self):
        while True:
            events = self.sel.select()  # 获得激活状态的事件
            for key, mask in events:
                callback = key.data  # 传入函数
                callback(key.fileobj, mask)  # mask暂时没有意义

    def accept(self, sock, mask):
        conn, addr = sock.accept()
        self.sel.register(conn, selectors.EVENT_READ, self.conn_read)

    def conn_read(self, conn, mask):
        if conn not in self.online_dict:
            if not self.auth(conn):
                print('验证不通过，关闭你')
        else:
            try:
                data = conn.recv(1024)
                if not data:
                    print('closing', conn)
                    self.sel.unregister(conn)
                    conn.close()
                    return
                print(data)
            except Exception:
                print('closing', conn)
                self.sel.unregister(conn)
                conn.close()

    def conn_write(self, conn, mask):
        pass

    def download(self, **info):
        # {'action':'downlod','file_name':'xxx','file_size':0}

        pass

    def auth(self, conn):
        config = configparser.ConfigParser()
        config.read(USER_DB_PATH)
        data = conn.recv(1024)
        data = data.decode('utf8')
        user_info = json.loads(data)
        # {'username':'xxxx','password':'xxx'}
        if config.has_section(user_info['username']):
            for conn in self.online_dict:
                print(self.online_dict[conn])
                if self.online_dict[conn]['username'] == user_info['username']:
                    status = struct.pack('i', AUTH_USER_HAS_LOGIN)
                    conn.send(status)
                    self.sel.unregister(conn)
                    conn.close()
                    return
            if user_info['password'] == config.get(user_info['username'], 'password'):
                status = struct.pack('i', AUTH_SUCCESS)
                conn.send(status)
                home_path = self.init_home(user_info['username'])
                self.online_dict[conn] = {'username': user_info['username'], 'home_path': home_path}
                return True
            else:
                # 密码错误
                status = struct.pack('i', AUTH_PASSWORD_NOT_CORRECT)
                conn.send(status)
                self.sel.unregister(conn)
                conn.close()
        else:
            # 不存在该用户
            status = struct.pack('i', AUTH_USER_NOT_EXIST)
            conn.send(status)
            self.sel.unregister(conn)
            conn.close()

    def init_home(self, username):
        home_dir = os.path.join(BASE_DIR, 'home')
        if not os.path.exists(home_dir):
            os.mkdir(home_dir)

        home_path = os.path.join(home_dir, username)
        if not os.path.exists(home_path):
            os.mkdir(home_path)

        return home_path
