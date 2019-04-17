#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs

from optparse import OptionParser
from random import randint
import random
import os, sys, json


parser = OptionParser()
parser.add_option("-p", "--program-size", dest="size", help="program size", default=None)
parser.add_option("-v", "--validate", action="store_true", dest="validate", help="program size", default=None)
parser.add_option("-r", dest="rand", action="store_true", help="Use non-deterministic algo")

# to turn validation on specify
#   multiple_solution: true
# in a problem specification


options, args = parser.parse_args()

if not options.rand:
    random.seed(1234)

if options.size is not None:
    ints = [randint(1, 100) for i in range(int(options.size))]
    _42 = random.randint(0, int(options.size) - 1)
    ints[_42] = 42
    print('\n'.join([str(x) for x in ints]))
    sys.exit(0)

# if validation option is set (-v or --validate)
# script fill use :
#    the first argument as   INPUT file path, this file should contain a problem input
#    the second argument as OUTPUT file path, this file should contain a student's solution
#
# this script must print out a valid json format as a result, even on error
if options.validate is not None:
    in_file = args[0]
    out_file = args[1]

    # following lines are testing whether given
    #       problem input aka INPUT
    #       and
    #       students answer aka OUTPUT
    #   is correct, this is used in cases where thay can be multiple solutions to a INPUT
    try:
        in_prop = sum([int(x) for x in open(in_file, 'r').read().split() if x])
        out_prop = int(open(args[1], 'r').read().strip())

        if in_prop == out_prop:
            result = {
                'result'    : 'ok',
                'difference': 0
            }
            print(json.dumps(result, indent=4))
            sys.exit(0)
        else:
            result = {
                'result'    : 'error',
                'difference': abs(in_prop - out_prop),
                'message'   : 'Expected sum of values to be %d but was %d' % (in_prop, out_prop),
                # entire json will be shown to a student, so quick descripton what was wrong can be useful
            }
            print(json.dumps(result, indent=4))
            sys.exit(1)

    except Exception as e:
        result = {
            'result'    : 'error',
            'details'   : 'invalid output file structure',
            'difference': -1
        }
        print(json.dumps(result, indent=4))
        sys.exit(1)

# normal algo
for line in sys.stdin:
    i = int(str(line).strip())
    if i == 42:
        break
    else:
        print(i)
print('wrong')
sys.exit(0)