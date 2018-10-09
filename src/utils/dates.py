#!/bin/python3
# author: Jan Hybs
from datetime import datetime


def get_datetime(dt=None):
    # return 'aaa'
    return (dt if dt else datetime.now()).strftime('%y%m%d_%H%M%S')