#!/bin/python3
# author: Jan Hybs
import datetime as dt
import re


def parse_dt(d):
    if d is None:
        return None
    if type(d) is dt.datetime:
        return d
    return dt.datetime(*list(map(int, re.split("[\D]+", d.strip()))))


class Role(object):
    ROOT = 'root'
    STUDENT = 'student'
    TEACHER = 'teacher'