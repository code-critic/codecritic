#!/bin/python3
# author: Jan Hybs
import os


def write_file(f, s, mode='w'):
    if f:
        os.makedirs(os.path.dirname(f), 0o777, True)
        if s is None:
            s = ''
        with open(f, mode) as fp:
            fp.write(s)


def read_file(f, mode='r'):
    if not f:
        return ''
    if not os.path.exists(f):
        return ''
    with open(f, mode) as fp:
        return fp.read()