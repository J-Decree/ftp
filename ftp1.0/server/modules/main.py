#!/usr/bin/env python
# coding=utf-8
import optparse
import os
import sys
import socketserver

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from conf.setting import *
from modules.ServerProvide import ServerProvide


class LogicHandler(object):
    def __init__(self):
        self.verify_args()

    def verify_args(self):
        # 系统传参处理
        op = optparse.OptionParser()
        # op.add_option('-s', '--server', dest='server')
        # op.add_option('-p', '--port', dest='port')
        options, args = op.parse_args()
        if not args:
            self.help()
            return
        arg = args[0]
        if hasattr(self, arg):
            func = getattr(self, arg)
            func()
        else:
            print('不存在的命令')

    def start(self):
        s = socketserver.ThreadingTCPServer(IP_PORT, ServerProvide)
        s.serve_forever()

    def help(self):
        print('help')
