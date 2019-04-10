#!/bin/python3
# author: Jan Hybs
import datetime as dt
import time
from threading import Semaphore

from flask import session
from flask_socketio import emit
from loguru import logger

import processing.request
from database.mongo import Mongo
from database.objects import User
from exceptions import ConfigurationException
from processing import ProcessRequestType
from www import socketio
from www.emittor import Emittor


namespace = None
queue = list()
thread_lock_max = 1
thread_lock = Semaphore(value=thread_lock_max)
mongo = Mongo()


def get_datetime(value=None):
    # return 'aaa'
    return (value if value else dt.datetime.now()).strftime('%y%m%d_%H%M%S')


def queue_status():
    return dict(
        items=queue,
        maximum=thread_lock_max,
        current=len(queue)
    )


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
    print('connected')
    Emittor.debug('ok, connected')


@socketio.on('debug')
def socket_debug(data):
    logger.info('debug {}', data)


@socketio.on('student-solution-submit', namespace=namespace)
def student_submit_solution(data):
    print(data)
    user = User(session['user'])

    try:
        type = str(data['type'])
        action = ProcessRequestType(type)
        skip_docker = not data.get('docker', True)
    except:
        Emittor.error(
            'Unsupported action',
            [
                'Given action is not supported:',
                '    %s' % data['type'],
                '',
                'Please contact jan.hybs@tul.cz',
                'if you think this is a mistake.'
            ]
        )
        return

    if not user.is_admin() and (skip_docker or action in (ProcessRequestType.GENERATE_INPUT, ProcessRequestType.GENERATE_OUTPUT)):
        Emittor.error(
            'Operation not permitted',
            [
                'You do not have sufficient privileges to perform action:',
                '    %s (skip docker: %s)' % (action, skip_docker),
                '',
                'Please contact jan.hybs@tul.cz',
                'if you want to gain the privileges.'
            ]
        )
        return

    request = processing.request.ProcessRequest(
        user=user,
        lang=data['lang'],
        problem=data['prob'],
        course=data['course'],
        solution=data['src'],
        type=action,
        docker=False if (skip_docker and user.is_admin()) else True,
    )

    mongo.save_log(request.get_log_dict())

    # ignore problems which are past due
    if request.problem.time_left < 0:
        return

    Emittor.register_events(request)
    Emittor.queue_status(queue_status())

    time.sleep(0.1)
    queue.append(request)
    Emittor.queue_push(request)

    time.sleep(0.1)

    # put a barrier here so only certain amount fo users can process code at once
    # while other will see queue list
    with thread_lock:
        try:
            request.process()
        except ConfigurationException as e:
            if user.is_admin():
                logger.exception('[visible to admin only] invalid yaml config')
                Emittor.exception(e)
        except Exception as e:
            logger.exception('process error:')
            Emittor.exception(e)
        finally:
            mongo.save_result(request.get_result_dict())
            request.save_result()
            request.destroy()

    queue.remove(request)
    Emittor.queue_pop(request)
