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
    import time

    size = 12333232
    p = ProcessBar(size)
    now_size = 0
    while size > now_size:
        #time.sleep(0.2)
        now_size += 10
        p.show_process(now_size)
