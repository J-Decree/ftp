import sys


class ProcessBar(object):
    def __init__(self, total_size):
        self.total_size = total_size

    def show_process(self, now_size):
        rail = round(now_size / self.total_size * 100, 1)
        s = ('#' * int(rail)).ljust(100 - int(rail), ' ') + ' %s%%\r' % rail
        sys.stdout.write(s)
        sys.stdout.flush()


if __name__ == '__main__':
    p = ProcessBar(132300)
    p.show_process(22333)