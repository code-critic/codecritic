#!/bin/python3
# author: Jan Hybs


def ensure_type(obj, cls, default=None):
    if obj is None:
        return default

    if isinstance(obj, cls):
        return obj

    try:
        return cls(obj)
    except:
        return default
