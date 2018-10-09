#!/usr/bin/env python
from collections import OrderedDict
from threading import Semaphore
import time
import os

from flask import Flask, render_template, session, redirect
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from cfg.env import variables as env
import threading

from cfg.languages import Lang
from cfg.problems import Prob
from processing import create_request, Processor
from utils.crypto import crypto
from utils.dates import get_datetime
from utils.io import write_file
from flask.json import JSONEncoder
import flask.json
from containers.docker import DockerAPI


import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'peek'):
            return obj.peek()
        return JSONEncoder.default(self, obj)


thread = None
stuff = None
start_time = time.time()
thread_lock_max = 1
thread_lock = Semaphore(value=thread_lock_max)

async_mode = 'threading'
namespace = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.root_path = env.www
app.json_encoder = CustomJSONEncoder
cors = CORS(app)
socketio = SocketIO(app, json=flask.json, async_mode=async_mode)


queue = OrderedDict()


# remove previous container on start and create new one
# DockerAPI.remove_container('ada19')
DockerAPI.create_container('korekontrol/ubuntu-java-python3', 'ada19', user=1000)


def queue_status():
    return dict(
        items=[v for v in queue.values()],
        maximum=thread_lock_max,
        current=len(queue)
    )


def redir():
    return redirect('/index')


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/')


@app.route('/')
@app.route('/index')
def index():
    if not 'user' in session:
        return redirect(env.web)

    return render_template(
        'socket.njk',
        user=session['user'],
        languages=Lang.instances,
        problems=Prob.groups(),
    )


@app.route('/login/<string:auth>')
def login(auth):
    user = crypto.decrypt_json(auth)
    user['email'] = user['eppn']
    user['name'] = user['eppn'].split('@')[0]
    user['affi'] = ', '.join(user['affiliation'].lower().replace('@tul.cz', '').split(';'))
    user['full_name'] = ' '.join([x.capitalize() for x in user['name'].split('.')])
    session['user'] = user
    return redirect('index')


py_test = '''
import sys
import time

for name in sys.stdin.read().splitlines():
    print("Hello, {name}!".format(name=name))
    #time.sleep(1)

'''.strip()

java_test = '''
import java.util.Scanner;

class main {

  public static void main(String[] args) {
    Scanner reader = new Scanner(System.in);

    while (reader.hasNextLine()){
        String name = reader.nextLine();
        System.out.format("Hello, %s!%n", name);
        //System.out.format("Hello, World!%n", name);
    }
    // String name = reader.nextLine();
    // System.out.format("Hello, %s!%n", name);
  }
}

'''.strip()


def broadcast_queue_status():
    # print('queue-status', queue_status())
    emit('queue-status', dict(status=200, queue=queue_status()))


def broadcast_queue_push(item):
    # print('queue-push', queue_status())
    emit('queue-push', dict(status=200, item=item), broadcast=True, include_self=False)


def broadcast_queue_pop(item):
    # print('queue-pop', queue_status())
    emit('queue-pop', dict(status=200, item=item), broadcast=True)


@socketio.on('connect')
def emit_market_data():
    pass


@socketio.on('student-solution-submit', namespace=namespace)
def student_submit_solution(data):
    user = session['user']['name']
    fullname = user + threading.current_thread().name

    request = create_request(
        user=user,
        prob_id=data['prob'],
        lang_id=data['lang'],
        src=data['src'],
        docker=True,
    )

    # ignore problems which are past due
    if request.prob.time_left < 0:
        Emittor.on_process_end(request)
        return

    # write source code
    write_file(request.config.get('filepath'), request.source_code)


    # if not data:
    #     request = create_request(
    #         user='jan.hybs',
    #         prob_id='T01',
    #         lang_id='PY3',
    #         docker=True,
    #     )
    #     write_file(request.config.get('filepath'), py_test)
    # else:
    #     request = create_request(
    #         user='jan.hybs',
    #         prob_id='T01',
    #         lang_id='JA10',
    #         docker=True,
    #     )
    #     write_file(request.config.get('filepath'), java_test)

    processor = Processor(request)
    register_events(processor)

    request.user = user
    broadcast_queue_status()
    broadcast_queue_push(request)
    queue[fullname] = request

    with thread_lock:
        result = processor.start()
        print(request)

        codes = [result.tests.get(test.id).result.value for test in request.prob.tests]
        result_location = os.path.join(
            env.results, request.user, request.prob.id,
            '%s_%s' % ('-'.join([str(x) for x in codes]), get_datetime())
        )

        Processor.write_result(request, result, location=result_location)

    del queue[fullname]
    broadcast_queue_pop(request)


def register_events(instance):
    instance.event_compile.on(
        Emittor.on_compile_start,
        Emittor.on_compile_end,
    )
    instance.event_execute.on(
        Emittor.on_execute_start,
        Emittor.on_execute_end,
    )
    instance.event_execute_test.on(
        Emittor.on_execute_test_start,
        Emittor.on_execute_test_end,
    )
    instance.event_process.on(
        Emittor.global_on_process_start,
        Emittor.global_on_process_end,
    )
    instance.event_process.on(
        Emittor.on_process_start,
        Emittor.on_process_end,
    )


class Emittor(object):

    @staticmethod
    def global_on_process_start(request):
        # print('process-start', request.peek())
        emit('process-start', dict(status=200, request=request, item=request), broadcast=True)

    @staticmethod
    def global_on_process_end(request):
        # print('process-end', request.peek())
        emit('process-end', dict(status=200, request=request, item=request), broadcast=True)

    # -----------------------------------------------------------------------------

    @staticmethod
    def on_compile_start(request, result):
        # print('compile-start-me', request.peek(), threading.current_thread().name)
        emit('compile-start-me', dict(status=200, request=request, result=result))

    @staticmethod
    def on_compile_end(request, result):
        # print('compile-end-me', request.peek(), threading.current_thread().name)
        emit('compile-end-me', dict(status=200, request=request, result=result))

    # -----------------------------------------------------------------------------

    @staticmethod
    def on_execute_test_start(request, test, result):
        # print('execute-test-start-me', request, test)
        emit('execute-test-start-me', dict(status=200, request=request, test=test, result=result))

    @staticmethod
    def on_execute_test_end(request, test, result):
        # print('execute-test-end-me', request, test)
        emit('execute-test-end-me', dict(status=200, request=request, test=test, result=result))

    # -----------------------------------------------------------------------------

    @staticmethod
    def on_execute_start(request, result):
        # print('execute-start-me', request.peek())
        emit('execute-start-me', dict(status=200, request=request, result=result))

    @staticmethod
    def on_execute_end(request, result):
        # print('execute-end-me', request.peek())
        emit('execute-end-me', dict(status=200, request=request, result=result))

    # -----------------------------------------------------------------------------

    @staticmethod
    def on_process_start(request):
        # print('process-start-me', request.peek())
        emit('process-start-me', dict(status=200, request=request, item=request))

    @staticmethod
    def on_process_end(request):
        # print('process-end-me', request.peek())
        emit('process-end-me', dict(status=200, request=request, item=request))


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=22122)
