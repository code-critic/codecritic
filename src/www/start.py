#!/bin/python3
# author: Jan Hybs
import argparse
import sys

from loguru import logger
from env import Env
from utils.io import delete_old_files
from flask_socketio import SocketIO
import flask


logger.configure(handlers=[
    dict(sink=sys.stdout),
    dict(sink=Env.log_file, colorize=True)
])


# app.run(debug=args.debug, host=args.host, port=args.port)

# from geventwebsocket import WebSocketServer
# # from gevent.pywsgi import WSGIServer
# http_server = WebSocketServer(('', 5000), app)
# http_server.serve_forever()


def parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--help', action='help', default=argparse.SUPPRESS,
                        help=argparse._('show this help message and exit'))

    flask_server = parser.add_argument_group('flask server')
    flask_server.add_argument('-p', '--port', type=int, default=5000)
    flask_server.add_argument('-h', '--host', type=str, default='127.0.0.1')
    flask_server.add_argument('-d', '--debug', action='store_true')
    flask_server.add_argument('-v', '--verbose', action='store_false')
    flask_server.add_argument('--backdoor', action='store_true')
    args = parser.parse_args()

    if args.verbose:
        # do not filter logger
        pass
    else:
        import logging

        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    return args


def register_routes(app, socketio):
    from www import auth
    from www import index
    from www import course
    from www import sockets
    from www import utils_www

    auth.register_routes(app, socketio)
    index.register_routes(app, socketio)
    course.register_routes(app, socketio)
    sockets.register_routes(app, socketio)
    utils_www.register_routes(app, socketio)


def main():
    args = parse_args()
    async_mode = 'gevent'  # eventlet, gevent_uwsgi, gevent, threading

    logger.info('Running automate version {}', Env.version)
    delete_old_files(Env.tmp)

    # -------------------------------------------------------------------------

    from www import app

    # -------------------------------------------------------------------------

    if args.debug:
        async_mode = 'threading'
    else:
        from gevent import monkey
        monkey.patch_all()

    # -------------------------------------------------------------------------

    socketio = SocketIO(app, json=flask.json, async_mode=async_mode, ping_interval=100 * 1000)
    register_routes(app, socketio)

    # -------------------------------------------------------------------------

    if args.backdoor:
        from www import backdoor
        backdoor.register_routes(app, socketio)

    # -------------------------------------------------------------------------

    logger.info('Listening on {host}:{port} (debug={debug})', **vars(args))
    info = '\n'.join(['{:>20s}: {:s}'.format(k, str(v)) for k, v in Env.info()])
    logger.info('Configuration in env.py:\n{}', info)
    logger.info('removing old files from {}', Env.tmp)

    # -------------------------------------------------------------------------

    if args.debug:
        app.run(debug=args.debug, host=args.host, port=args.port)
    else:
        from geventwebsocket import WebSocketServer
        http_server = WebSocketServer((args.host, args.port), app)
        http_server.serve_forever()


    return app, args


if __name__ == '__main__':
    main()

