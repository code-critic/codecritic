#!/bin/python3
# author: Jan Hybs

import os
import sys
from collections import namedtuple

_variables_cls = namedtuple('Vars',[
    'src', 'cfg', 'data', 'root',
    'queue', 'www', 'tmp', 'results', 'web', 'worker', 'database'
])

_root = root=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
variables = _variables_cls(
    root=_root,
    src=os.path.join(_root, 'src'),
    cfg=os.path.join(_root, 'cfg'),
    data=os.path.join(_root, 'data'),
    queue=os.path.join(_root, 'queue'),
    www=os.path.join(_root, 'www'),
    tmp=os.path.join(_root, 'tmp'),
    results=os.path.join(_root, 'results'),
    web='https://hybs.nti.tul.cz',
    worker='http://hybsntb.nti.tul.cz:22122',

    db=os.path.join(_root, 'database'),
)


class Env(object):
    root = _root
    src = os.path.join(_root, 'src')
    cfg = os.path.join(_root, 'cfg')
    tmp = os.path.join(_root, '.tmp')
    problems = os.path.join(_root, 'problems')

    problem_timeout = 60.0
    teacher_timeout = 60.0 * 10

    fonts = os.path.join(_root, 'www', 'fonts')
    url_slave = 'http://hybs.nti.tul.cz:5000'
    url_login = 'https://flowdb.nti.tul.cz/secure'
    url_logout = 'https://flowdb.nti.tul.cz/Shibboleth.sso/Logout'

    secret_key_file = os.path.join(_root, '.secret')

    @classmethod
    def secret_key(cls):
        with open(cls.secret_key_file, 'r') as fp:
            return fp.read().strip()

