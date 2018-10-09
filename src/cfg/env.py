#!/bin/python3
# author: Jan Hybs

import os
import sys
from collections import namedtuple

_variables_cls = namedtuple('Vars',[
    'src', 'cfg', 'data', 'root', 'lang_conf', 'prob_conf',
    'queue', 'www', 'tmp', 'results', 'web', 'worker'
])

_root = root=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
variables = _variables_cls(
    root=_root,
    src=os.path.join(_root, 'src'),
    cfg=os.path.join(_root, 'cfg'),
    data=os.path.join(_root, 'data'),
    lang_conf=os.path.join(_root, 'cfg', 'languages.yaml'),
    prob_conf=os.path.join(_root, 'cfg', 'problems.yaml'),
    queue=os.path.join(_root, 'queue'),
    www=os.path.join(_root, 'www'),
    tmp=os.path.join(_root, 'tmp'),
    results=os.path.join(_root, 'results'),
    web='https://hybs.nti.tul.cz',
    worker='http://hybsntb.nti.tul.cz:22122'
)
