#!/bin/python3
# author: Jan Hybs

import re

_find_package_regex = re.compile(r'^\s*(package\s+[a-zA-Z0-9_.]+;)$', re.MULTILINE)
_find_main_regex = re.compile(r'^(public\s+class\s+[a-zA-Z0-9_]+\s*{\s*)$')


def fix_java_solution(content: str):
    result = content.splitlines()
    for i, l in enumerate(result):
        if _find_main_regex.match(l):
            result[i] = _find_main_regex.sub(r'public class main {', l)
            break
    return _find_package_regex.sub(r'// \1', '\n'.join(result))
