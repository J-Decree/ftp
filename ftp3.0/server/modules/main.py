import optparse
from .ServerHandler import ServerHandler


class LogicHandler(object):
    def __init__(self):
        self.verify_args()

    def verify_args(self):
        option = optparse.OptionParser()
        # option.add_option('-s','--server',dest='server')
        options, args = option.parse_args()
        if len(args) != 1:
            self.help()
            return
        arg = args[0]
        if hasattr(self, arg):
            func = getattr(self, arg)
            func()

    def help(self):
        print('example:python server.py start')

    def start(self):
        s = ServerHandler()
        s.run()


if __name__ == '__main__':
    pass
