#!/bin/python3
# author: Jan Hybs
import argparse
import sys

from loguru import logger
from env import Env


logger.configure(handlers=[
    dict(sink=sys.stdout),
    dict(sink=Env.log_file, colorize=True)
])


from entities.crates import CaseResult


c = CaseResult(
    id='self.id',
    status='self.status.str',
    cmd='self.cmd',
    duration=1.3,
    returncode=0,
    console=None,
    message='self.message',
    message_details=None,
    attachments=list(),
    score=151651,
    scores=[13, 65, 8],
)

# app.run(debug=args.debug, host=args.host, port=args.port)

# from geventwebsocket import WebSocketServer
# # from gevent.pywsgi import WSGIServer
# http_server = WebSocketServer(('', 5000), app)
# http_server.serve_forever()


def parse_args(cargs=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--help', action='help', default=argparse.SUPPRESS,
                        help=argparse._('show this help message and exit'))

    flask_server = parser.add_argument_group('flask server')
    flask_server.add_argument('-p', '--port', type=int, default=5000)
    flask_server.add_argument('-h', '--host', type=str, default='127.0.0.1')
    flask_server.add_argument('-d', '--debug', action='store_true')
    flask_server.add_argument('-v', '--verbose', action='store_true')
    flask_server.add_argument('--backdoor', action='store_true')
    args = parser.parse_args(cargs)

    if args.verbose:
        # do not filter logger
        pass
    else:
        import logging
        logger.info('supressing flask warnings')
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    return args


def register_routes(app, socketio):
    from www import auth
    from www import index
    from www import course
    from www import sockets
    from www import stats
    from www import utils_www

    auth.register_routes(app, socketio)
    index.register_routes(app, socketio)
    course.register_routes(app, socketio)
    sockets.register_routes(app, socketio)
    stats.register_routes(app, socketio)
    utils_www.register_routes(app, socketio)


o = {
    "_id" : "5cc6be848bfa8a5da73d17e9",
    "lang" : "CPP",
    "solution" : "#include <iostream>\r\nusing namespace std;\r\n\r\nint main() \r\n{\r\n    cout << 10 << endl;\r\n    cout << 15 << endl;\r\n    cout << 46 << endl;\r\n    return 0;\r\n}",
    "docker" : False,
    "action" : "solve",
    "user" : "root",
    "course" : "TST-2019",
    "problem" : "problem-1",
    "result" : {
        "id" : "Result",
        "status" : "answer-wrong",
        "duration" : 9.69145011901855,
        "returncode" : None,
        "message" : "Submitted solution is wrong",
        "score" : 10006,
        "scores" : [
            1,
            0,
            6
        ]
    },
    "results" : [
        {
            "id" : "Compilation",
            "status" : "ok",
            "cmd" : "g++ main.cpp -o main",
            "duration" : 7.35814046859741,
            "returncode" : 0,
            "score" : 0,
            "scores" : []
        },
        {
            "id" : "case-1.s",
            "status" : "answer-correct",
            "cmd" : "./main",
            "duration" : 0.0785830020904541,
            "returncode" : 0,
            "message" : "Submitted solution is correct",
            "score" : 0,
            "scores" : []
        },
        {
            "id" : "case-2",
            "status" : "answer-wrong",
            "cmd" : "./main",
            "duration" : 0.0173075199127197,
            "returncode" : 0,
            "message" : "Submitted solution is incorrect",
            "score" : 0,
            "scores" : []
        },
        {
            "id" : "case-3.0",
            "status" : "answer-wrong",
            "cmd" : "./main",
            "duration" : 0.0140361785888672,
            "returncode" : 0,
            "message" : "Submitted solution is incorrect",
            "score" : 0,
            "scores" : []
        },
        {
            "id" : "case-3.1",
            "status" : "answer-wrong",
            "cmd" : "./main",
            "duration" : 0.0361495018005371,
            "returncode" : 0,
            "message" : "Submitted solution is incorrect",
            "score" : 0,
            "scores" : []
        },
        {
            "id" : "case-3.2",
            "status" : "answer-wrong",
            "cmd" : "./main",
            "duration" : 0.0138497352600098,
            "returncode" : 0,
            "message" : "Submitted solution is incorrect",
            "score" : 0,
            "scores" : []
        },
        {
            "id" : "case-3.3",
            "status" : "answer-wrong",
            "cmd" : "./main",
            "duration" : 0.0343863964080811,
            "returncode" : 0,
            "message" : "Submitted solution is incorrect",
            "score" : 0,
            "scores" : []
        },
        {
            "id" : "case-3.4",
            "status" : "answer-wrong",
            "cmd" : "./main",
            "duration" : 0.0512194633483887,
            "returncode" : 0,
            "message" : "Submitted solution is incorrect",
            "score" : 0,
            "scores" : []
        }
    ],
    "output_dir" : "courses/course-template/2019/results/root/problem-1/348-200-W-answer-wrong",
    "attempt" : 348
}


def main():
    args = parse_args()
    async_mode = 'gevent'  # eventlet, gevent_uwsgi, gevent, threading

    logger.info('Running automate version {}', Env.version)
    from utils.io import delete_old_files
    delete_old_files(Env.tmp)

    # -------------------------------------------------------------------------

    if args.debug:
        async_mode = 'threading'
        Env.debug_mode = True
    else:
        from gevent import monkey
        monkey.patch_all()

    # -------------------------------------------------------------------------

    from flask_socketio import SocketIO
    import flask
    from www import app

    # -------------------------------------------------------------------------

    socketio = SocketIO(app, json=flask.json, async_mode=async_mode, ping_interval=100 * 1000)
    register_routes(app, socketio)

    # -------------------------------------------------------------------------

    if args.backdoor:
        from www import backdoor
        backdoor.register_routes(app, socketio)

    # -------------------------------------------------------------------------

    logger.info('Listening on {host}:{port} (debug={debug})', **vars(args))
    Env.dump_info('Configuration in env.py')
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
    # import difflib
    # from pathlib import Path
    #
    # p = '4.1'
    # # p = '5.0'
    # a = Path('/home/jan-hybs/projects/cc/codecritic/.tmp/a.%s' % p).read_text().splitlines()
    # b = Path('/home/jan-hybs/projects/cc/codecritic/.tmp/b.%s' % p).read_text().splitlines()
    #
    # def j(x):
    #     print('!', x)
    #     return x in "\nx"
    #
    # diff = difflib.SequenceMatcher(j, a, b).ratio()
    # diff = difflib.HtmlDiff(charjunk=j)
    # f = diff.make_file(a, b)
    #
    # Path('foo.html').write_text(f)


