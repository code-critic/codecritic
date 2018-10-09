#!/bin/python3
# author: Jan Hybs

import random
import string


def random_string(l):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(l))