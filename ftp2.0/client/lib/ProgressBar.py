class ProgressBar(object):
    def __init__(self, total_size, bar_len=50):
        self.total_size = total_size
        if bar_len < 50:
            self.bar_len = 50
        else:
            self.bar_len = bar_len

    def show_progress(self, now_size):
        rate = now_size / self.total_size
        finished_len = int(rate * self.bar_len)
        unfinish_len = self.bar_len - finished_len
        rate = round(rate * 100, 1)
        s = '[%s%s] %s%%\r' % ('>' * finished_len, '-' * unfinish_len, rate)
        print(s, flush=True, end='')


if __name__ == '__main__':
    p = ProgressBar(1993342)
    p.show_progress(323243)
