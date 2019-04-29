#!/bin/python3
# author: Jan Hybs

import pytest
import unittest
import os
import sys

from www import start
from loguru import logger

case = unittest.TestCase('__init__')
logger.configure(
    handlers=[dict(sink=sys.stdout, colorize=False, level='INFO')]
)


# -----------------------------------------------------------------------------


@pytest.mark.www
def test_parser():
    args = start.parse_args(['-h', '0.0.0.0'])

    case.assertEqual(args.port, 5000)
    case.assertEqual(args.host, '0.0.0.0')
    case.assertIs(args.backdoor, False)


@pytest.mark.www
def test_server():
    from env import Env
    Env.use_database = False

    from www import app
    from flask_socketio import SocketIO
    import flask

    async_mode = 'threading'
    socketio = SocketIO(app, json=flask.json, async_mode=async_mode, ping_interval=100 * 1000)

    from www import backdoor
    backdoor.register_routes(app, socketio)
    start.register_routes(app, socketio)


@pytest.mark.www
def test_remove_old():
    from env import Env
    from loguru import logger

    Env.dump_info('Configuration in env.py')
    from utils import io
    # delete old files so the test is not influenced
    io.delete_old_files(Env.tmp, io.HALF_DAY)

    foo = Env.tmp.joinpath('foo')
    foo.mkdir(parents=True, exist_ok=True)
    bar = foo.joinpath('bar.txt')
    bar.touch()

    case.assertEqual(io.delete_old_files(Env.tmp, io.ONE_DAY), 0)

    os.utime(str(foo), (0, 0))
    case.assertEqual(io.delete_old_files(Env.tmp, io.ONE_DAY), 1)
