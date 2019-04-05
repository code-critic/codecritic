#!/bin/python3
# author: Jan Hybs

import random
import string
import typing
import hashlib


def random_string(l):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(l))


def ensure_iterable(it) -> typing.List[typing.Any]:

    if it is None:
        return []

    if isinstance(it, list):
        return list(it)

    return [it]


def string_hash(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % (10 ** 8)
