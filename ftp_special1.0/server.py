from socket import *
import select
import json
import struct
import os

IP_PORT = ('localhost', 8888)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
upload_dic = {}
download_dic = {}


class ServerHandler(object):
    def __init__(self):
        self.sock = socket()
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.bind(IP_PORT)
        self.sock.setblocking(False)
        self.read_list = [self.sock, ]
        self.write_list = []
        self.except_list = []

    def download(self, conn, **info):
        print('download.............')
        # action_dict = {'action': 'download', 'filename': file_name}
        file_name = info.get('filename')
        file_path = os.path.join(BASE_DIR, file_name)
        print(file_path)
        if not os.path.exists(file_path):
            status = struct.pack('b', 101)
            conn.send(status)
            print('nononon')
            return
        else:
            file_size = os.path.getsize(file_path)
            status = struct.pack('b', 100)
            size = struct.pack('i', file_size)
            print(status, size)
            conn.send(status)
            conn.send(size)
            f = open(file_path, 'rb')
            download_dic[conn] = [f, file_size]
        print('upload function end .......')

    def upload(self, conn, **info):
        print('upload 。。。。。。。。。')
        file_name = info.get('filename')
        file_size = info.get('filesize')
        f = open('%s_%s.pdf' % (file_name, conn), 'wb')
        upload_dic[conn] = [f, file_size]
        print('upload function end ......')

    def start(self):
        self.sock.listen(5)
        while True:
            rl, wl, xl = select.select(self.read_list, self.write_list, self.except_list)
            for rsock in rl:
                if rsock == self.sock:
                    conn, addr = rsock.accept()
                    self.read_list.append(conn)
                    self.write_list.append(conn)
                    self.except_list.append(conn)
                else:
                    data = rsock.recv(1024)
                    data2 = data
                    if data:
                        try:
                            data = data.decode('utf8')
                            # 假设是json请求
                            info = json.loads(data)
                            action = info['action']
                            if hasattr(self, action):
                                func = getattr(self, action)
                                func(rsock, **info)
                            else:
                                raise Exception('dffdsda')
                        except Exception as e:
                            if rsock in upload_dic:
                                f = upload_dic[rsock][0]
                                file_size = upload_dic[rsock][1]
                                if file_size:
                                    f.write(data2)
                                    f.flush()
                                    upload_dic[rsock][1] -= len(data2)
                                    if upload_dic[rsock][1] <= 0:
                                        print('上传完毕了')
                                        f.close()
                                        del upload_dic[rsock]
                            else:
                                print(data)
                    else:
                        rsock.close()

            for wsock in wl:
                if wsock in download_dic:
                    info_list = download_dic[wsock]
                    f = info_list[0]
                    file_size = info_list[1]
                    if file_size:
                        data = f.read(1024)
                        print(data)
                        wsock.send(data)
                        file_size -= len(data)
                        if file_size <= 0:
                            f.close()
                            del download_dic[wsock]
                        else:
                            info_list[1] = file_size

            for xsock in xl:
                xsock.close()


if __name__ == '__main__':
    s = ServerHandler()
    s.start()
