#!/bin/python3
# author: Jan Hybs


import pathlib
import sys


sys.path.extend([
    str(pathlib.Path(__file__).resolve().parent.parent / 'tests'),
    str(pathlib.Path(__file__).resolve().parent.parent / 'src'),
    str(pathlib.Path(__file__).resolve().parent.parent / 'build'),
])
