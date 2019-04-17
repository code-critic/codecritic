#!/bin/python3
# author: Jan Hybs

import pytest
import unittest
from www import start

case = unittest.TestCase('__init__')


@pytest.mark.www
def test_server():
    args = start.parse_args(['-h', '0.0.0.0'])

    case.assertEqual(args.port, 5000)
    case.assertEqual(args.host, '0.0.0.0')
    case.assertIs(args.backdoor, False)
