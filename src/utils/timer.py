#!/usr/bin/python
# author: Jan Hybs


import time


class Timer(object):
    def __init__(self, name=None, log=None):
        self.start_time = None
        self.stop_time = None
        self.name = name
        self.log = log

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_time = time.time()
        if self.log:
            self.log(str(self))
        return False

    @staticmethod
    def decorate(name=None, log=None):
        def real_decorator(function):
            def wrapper(*args, **kwargs):
                with Timer(name, log):
                    result = function(*args, **kwargs)
                return result
            return wrapper
        return real_decorator

    @property
    def duration(self):
        if self.stop_time:
            return self.stop_time - self.start_time
        else:
            return time.time() - self.start_time

    @property
    def micro(self):
        return self.duration * 1000.0

    @property
    def pretty_duration(self):
        return time.strftime('%H:%M:%S', time.gmtime(int(self.duration)))

    @property
    def pretty_duration_micro(self):
        micro = ('%1.3f' % (self.duration - int(self.duration)))[2:]
        return time.strftime('%H:%M:%S', time.gmtime(int(self.duration))) + '.' + micro

    def __repr__(self):
        if self.name:
            return '[{self.micro:8.2f} ms] in {self.name:20}'.format(self=self)
        return self.pretty_duration_micro
