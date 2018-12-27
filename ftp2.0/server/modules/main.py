import optparse
import socketserver
from modules.ServerHandler import ServerHandler
from conf.setting import IP_PORT


class LogicHandler(object):
    def __init__(self):
        self.verify_args()

    def verify_args(self):
        op = optparse.OptionParser()
        options, args = op.parse_args()

        if len(args) == 1:
            cmd = args[0]
            if hasattr(self, cmd):
                func = getattr(self, cmd)
                func()
                return True
        self.help()

    def start(self):
        print('server is working ....')
        s = socketserver.ThreadingTCPServer(IP_PORT, ServerHandler)
        s.serve_forever()

    def help(self):
        print('Example: python ftpserver.py start')


if __name__ == '__main__':
    LogicHandler()
