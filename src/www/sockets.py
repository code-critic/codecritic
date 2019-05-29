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
from env import Env
from exceptions import ConfigurationException
from processing import ProcessRequestType
from www.emittor import Emittor


namespace = None
queue = list()
thread_lock_max = 10
thread_lock = Semaphore(value=thread_lock_max)


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


def _process_solution(user, action, skip_docker, problem_id, course_id, lang_id=None, src=None, _id=None):
    if not user.is_admin() and (
            skip_docker or action in (ProcessRequestType.GENERATE_INPUT, ProcessRequestType.GENERATE_OUTPUT)):
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
        lang=lang_id,
        problem=problem_id,
        course=course_id,
        src=src,
        type=action,
        docker=False if (skip_docker and user.is_admin()) else True,
    )

    if Env.use_database:
        Mongo().save_log(request.get_log_dict())

    # ignore problems which are past due
    if request.problem.time_left < 0:
        return

    Emittor.register_events(request)
    Emittor.queue_status(queue_status())
    queue.append(request)
    Emittor.queue_push(request)

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
            output_dir, attempt = request.save_result()
            if Env.use_database:
                # replace document instead of creating new one
                Mongo().save_result(
                    request.get_result_dict(),
                    _id=_id,
                    output_dir=output_dir,
                    attempt=attempt,
                )
            request.destroy()

    queue.remove(request)
    Emittor.queue_pop(request)


def register_routes(app, socketio):
    @socketio.on('connect')
    def emit_market_data():
        print('connected')
        Emittor.debug('ok, connected')

    @socketio.on('debug')
    def socket_debug(data):
        Emittor.debug('ok, connected' + str(data))

    @socketio.on('student-process-solution', namespace=namespace)
    def student_process_solution(data):
        print(data)
        user = User(session['user'])
        try:
            document = Mongo().result_by_id(data['_id'])
            _process_solution(
                user=user,
                action=document.action,
                skip_docker=not document.docker,
                problem_id=document.problem,
                course_id=document.course,
                lang_id=document.lang,
                src=document.solution,
                _id=data['_id'],
            )
        except:
            logger.exception('Error while processing solution')

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
            src=data['src'],
            type=action,
            docker=False if (skip_docker and user.is_admin()) else True,
        )

        if Env.use_database:
            Mongo().save_log(request.get_log_dict())

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
                output_dir, attempt = request.save_result()
                if Env.use_database:
                    Mongo().save_result(
                        request.get_result_dict(),
                        output_dir=output_dir,
                        attempt=attempt,
                    )
                request.destroy()

        queue.remove(request)
        Emittor.queue_pop(request)
