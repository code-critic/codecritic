# import os, sys
#
# sys.path.append('src')
# import time
# from datetime import datetime
# from threading import Semaphore
# from collections import OrderedDict
#
# from flask import Flask, session, redirect, render_template
# from flask_sso import SSO
# from flask import Flask, render_template, session, request
# from flask_cors import CORS
# from flask_socketio import SocketIO, emit
# from cfg.env import variables as env
# import threading
# from processing import create_request, Processor
# from utils.io import write_file
# from flask.json import JSONEncoder
# import flask.json
# from containers.docker import DockerAPI
#
# import logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)
#
#
# class CustomJSONEncoder(JSONEncoder):
#     def default(self, obj):
#         if hasattr(obj, 'peek'):
#             return obj.peek()
#         return JSONEncoder.default(self, obj)
#
#
# # https://hybs.nti.tul.cz/
# def get_user_session_info(key):
#     return session['user'].get(
#         key,
#         'Key `{0}` not found in user session info'.format(key)
#     )
#
#
# def get_user_details(fields):
#     defs = [
#         '<dt>{0}</dt><dd>{1}</dd>'.format(f, get_user_session_info(f))
#         for f in fields
#     ]
#     return '<dl>{0}</dl>'.format(''.join(defs))
#
#
# def register_events(instance):
#     instance.event_compile.on(
#         Emittor.on_compile_start,
#         Emittor.on_compile_end,
#     )
#     instance.event_execute.on(
#         Emittor.on_execute_start,
#         Emittor.on_execute_end,
#     )
#     instance.event_execute_test.on(
#         Emittor.on_execute_test_start,
#         Emittor.on_execute_test_end,
#     )
#     instance.event_process.on(
#         Emittor.global_on_process_start,
#         Emittor.global_on_process_end,
#     )
#     instance.event_process.on(
#         Emittor.on_process_start,
#         Emittor.on_process_end,
#     )
#
#
# class Emittor(object):
#
#     @staticmethod
#     def global_on_process_start(request):
#         # print('process-start', request.peek())
#         emit('process-start', dict(status=200, request=request, item=request), broadcast=True)
#
#     @staticmethod
#     def global_on_process_end(request):
#         # print('process-end', request.peek())
#         emit('process-end', dict(status=200, request=request, item=request), broadcast=True)
#
#     # -----------------------------------------------------------------------------
#
#     @staticmethod
#     def on_compile_start(request, result):
#         # print('compile-start-me', request.peek(), threading.current_thread().name)
#         emit('compile-start-me', dict(status=200, request=request, result=result))
#
#     @staticmethod
#     def on_compile_end(request, result):
#         # print('compile-end-me', request.peek(), threading.current_thread().name)
#         emit('compile-end-me', dict(status=200, request=request, result=result))
#
#     # -----------------------------------------------------------------------------
#
#     @staticmethod
#     def on_execute_test_start(request, test, result):
#         # print('execute-test-start-me', request, test)
#         emit('execute-test-start-me', dict(status=200, request=request, test=test, result=result))
#
#     @staticmethod
#     def on_execute_test_end(request, test, result):
#         # print('execute-test-end-me', request, test)
#         emit('execute-test-end-me', dict(status=200, request=request, test=test, result=result))
#
#     # -----------------------------------------------------------------------------
#
#     @staticmethod
#     def on_execute_start(request, result):
#         # print('execute-start-me', request.peek())
#         emit('execute-start-me', dict(status=200, request=request, result=result))
#
#     @staticmethod
#     def on_execute_end(request, result):
#         # print('execute-end-me', request.peek())
#         emit('execute-end-me', dict(status=200, request=request, result=result))
#
#     # -----------------------------------------------------------------------------
#
#     @staticmethod
#     def on_process_start(request):
#         # print('process-start-me', request.peek())
#         emit('process-start-me', dict(status=200, request=request, item=request))
#
#     @staticmethod
#     def on_process_end(request):
#         # print('process-end-me', request.peek())
#         emit('process-end-me', dict(status=200, request=request, item=request))
#
#
# def create_app():
#     app = Flask('SSOTutorial')
#     app.secret_key = 'cH\xc5\xd9\xd2\xc4,^\x8c\x9f3S\x94Y\xe5\xc7!\x06>AAAVDS'
#
#     thread = None
#     stuff = None
#     start_time = time.time()
#     thread_lock_max = 1
#     thread_lock = Semaphore(value=thread_lock_max)
#
#     async_mode = 'threading'
#     async_mode = None
#     namespace = None
#
#     app = Flask(__name__)
#     app.config['SECRET_KEY'] = 'secret!'
#     app.root_path = env.www
#     app.json_encoder = CustomJSONEncoder
#     cors = CORS(app)
#     socketio = SocketIO(app, json=flask.json, async_mode=async_mode)
#
#     queue = OrderedDict()
#
#     SSO_ATTRIBUTE_MAP = {
#         'persistent-id':    (True, 'persistent-id'),
#         'eppn':             (True, 'eppn'),
#         'affiliation':      (True, 'affiliation'),
#     }
#     app.config.setdefault('SSO_ATTRIBUTE_MAP', SSO_ATTRIBUTE_MAP)
#     app.config.setdefault('SSO_LOGIN_URL', '/secure')
#
#     ext = SSO(app=app)
#     # ext = SSO(app=socketio)
#
#     def queue_status():
#         return dict(
#             items=[v for v in queue.values()],
#             maximum=thread_lock_max,
#             current=len(queue)
#         )
#
#     @ext.login_handler
#     def login(user_info):
#         session['user'] = user_info
#         return redirect('/')
#
#     @app.route('/logout')
#     def logout():
#         session.pop('user')
#         return redirect('/')
#
#     @app.route('/')
#     def index():
#         if 'user' not in session:
#             return redirect('/secure')
#
#         return redirect('/?foo=bar')
#         return render_template('socket.njk', **dict(user=session['user']))
#
#     py_test = '''
#     import sys
#     import time
#
#     for name in sys.stdin.read().splitlines():
#         print("Hello, {name}!".format(name=name))
#         #time.sleep(1)
#
#     '''.strip()
#
#     java_test = '''
#     import java.util.Scanner;
#
#     class main {
#
#       public static void main(String[] args) {
#         Scanner reader = new Scanner(System.in);
#
#         while (reader.hasNextLine()){
#             String name = reader.nextLine();
#             System.out.format("Hello, %s!%n", name);
#             //System.out.format("Hello, World!%n", name);
#         }
#         // String name = reader.nextLine();
#         // System.out.format("Hello, %s!%n", name);
#       }
#     }
#
#     '''.strip()
#
#     def broadcast_queue_status():
#         # print('queue-status', queue_status())
#         emit('queue-status', dict(status=200, queue=queue_status()))
#
#     def broadcast_queue_push(item):
#         # print('queue-push', queue_status())
#         emit('queue-push', dict(status=200, item=item), broadcast=True, include_self=False)
#
#     def broadcast_queue_pop(item):
#         # print('queue-pop', queue_status())
#         emit('queue-pop', dict(status=200, item=item), broadcast=True)
#
#     @socketio.on('connect')
#     def emit_market_data():
#         print('connected')
#         pass
#
#     @socketio.on('student-solution-submit', namespace=namespace)
#     def student_submit_solution(data):
#         name = threading.current_thread().name
#
#         if not data:
#             request = create_request(
#                 user='jan.hybs',
#                 prob_id='T01',
#                 lang_id='PY3',
#                 docker=True,
#             )
#             write_file(request.config.get('filepath'), py_test)
#         else:
#             request = create_request(
#                 user='jan.hybs',
#                 prob_id='T01',
#                 lang_id='JA10',
#                 docker=True,
#             )
#             write_file(request.config.get('filepath'), java_test)
#
#         processor = Processor(request)
#         register_events(processor)
#
#         request.user = name
#         broadcast_queue_status()
#         broadcast_queue_push(request)
#         queue[name] = request
#
#         with thread_lock:
#             result = processor.start()
#
#         del queue[name]
#         broadcast_queue_pop(request)
#
#     return app
#
#
# def wsgi(*args, **kwargs):
#     return create_app()(*args, **kwargs)
#
#
# if __name__ == '__main__':
#     create_app().run(debug=True, port=8000, host='0.0.0.0')
#

import sys
sys.path.append('src')
from flask import Flask, session, redirect
from flask_sso import SSO
from utils.crypto import crypto
from cfg.env import variables as env


def create_app():
    app = Flask('SSOTutorial')
    app.secret_key = 'cH\xc5\xd9\xd2\xc4,^\x8c\x9f3S\x94Y\xe5\xc7!\x06>AAAVDS'

    SSO_ATTRIBUTE_MAP = {
        'persistent-id':    (True, 'persistent-id'),
        'eppn':             (True, 'eppn'),
        'affiliation':      (True, 'affiliation'),
    }
    app.config.setdefault('SSO_ATTRIBUTE_MAP', SSO_ATTRIBUTE_MAP)
    app.config.setdefault('SSO_LOGIN_URL', '/secure')

    ext = SSO(app=app)

    @ext.login_handler
    def login(user_info):
        session['user'] = user_info
        return redirect('/')

    @app.route('/logout')
    def logout():
        session.pop('user')
        return redirect('/')

    @app.route('/')
    def index():
        if 'user' not in session:
            return redirect('/secure')

        args = crypto.encrypt_json(session['user'])
        url = env.worker + '/login/' + args

        return redirect(url)
        # return render_template('socket.njk', **dict(user=session['user']))

    return app


def wsgi(*args, **kwargs):
    return create_app()(*args, **kwargs)


if __name__ == '__main__':
    create_app().run(debug=True, port=8000, host='0.0.0.0')

# https://hybs.nti.tul.cz/