#!/usr/bin/env python3
# author: Jan Hybs

import subprocess
import argparse
import os
import sys
import time

from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('---i', default=None)
parser.add_argument('---o', default='/dev/null')
parser.add_argument('---e', default='/dev/null')
parser.add_argument('---t', type=int, default=60)
parser.add_argument('---w', default=None)

args, rest = parser.parse_known_args()

# change dir
if args.w:
    os.chdir(args.w)

# set fp's
in_fp = None if not args.i else Path(args.i).open('r')
out_fp = Path(args.o).open('w')
if args.o == args.e:
    err_fp = subprocess.STDOUT
else:
    err_fp = Path(args.e).open('w')

# -----------------------------------------------

try:
    process = subprocess.Popen(rest, stdin=in_fp, stdout=out_fp, stderr=err_fp)
except Exception as ex:
    print(667)
    print(0.0)
    sys.exit(0)

# -----------------------------------------------

st = time.time()
try:
    rc = process.wait(args.t)
except subprocess.TimeoutExpired as ex:
    process.kill()
    rc = 666
et = time.time()

# -----------------------------------------------

print(rc)
print('%1.3f' % (et - st))
sys.exit(0)