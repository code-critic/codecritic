#!/bin/python3
# author: Jan Hybs

import pytest
import unittest
from www import start

case = unittest.TestCase('__init__')


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
    start.register_routes(app, socketio)
