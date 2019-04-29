#!/bin/python3
# author: Jan Hybs
import time
import traceback

from flask_socketio import emit
from loguru import logger
from exceptions import FatalException, CompileException
from processing.request import ProcessRequest


class Emittor(object):
    @staticmethod
    def register_events(instance: ProcessRequest):
        instance.event_compile.on(
            Emittor.on_compile_start,
            Emittor.on_compile_end,
        )
        # instance.event_execute.on(
        #     Emittor.on_execute_start,
        #     Emittor.on_execute_end,
        # )
        instance.event_execute_test.on(
            Emittor.on_execute_test_start,
            Emittor.on_execute_test_end,
        )
        # instance.event_process.on(
        #     Emittor.global_on_process_start,
        #     Emittor.global_on_process_end,
        # )
        instance.event_process.on(
            Emittor.on_process_start,
            Emittor.on_process_end,
        )

    @classmethod
    def global_on_process_start(cls, request):
        data = dict(status=200, data=request)
        return cls._event('process-start', data, broadcast=True, include_self=False)

    @classmethod
    def global_on_process_end(cls, request):
        data = dict(status=200, data=request)
        return cls._event('process-end', data, broadcast=True, include_self=False)

    # -----------------------------------------------------------------------------

    @classmethod
    def on_compile_start(cls, result):
        return cls.event('compile-start-me', result)

    @classmethod
    def on_compile_end(cls, result):
        return cls.event('compile-end-me', result)

    # -----------------------------------------------------------------------------

    @classmethod
    def on_execute_test_start(cls, test):
        return cls.event('execute-test-start-me', test)

    @classmethod
    def on_execute_test_end(cls, test):
        return cls.event('execute-test-end-me', test)

    # -----------------------------------------------------------------------------

    # @classmethod
    # def on_execute_start(cls, request, result):
    #     return cls.event('execute-start-me', request, result=result)
    #
    # @classmethod
    # def on_execute_end(cls, request, result):
    #     return cls.event('execute-end-me', request, result=result)

    # -----------------------------------------------------------------------------

    @classmethod
    def on_process_start(cls, result):
        return cls.event('process-start-me', result)

    @classmethod
    def on_process_end(cls, result):
        return cls.event('process-end-me', result)

    # -----------------------------------------------------------------------------

    @classmethod
    def debug(cls, data):
        return cls.event('debug', data)

    @classmethod
    def queue_push(cls, data):
        return cls._event('queue-push', dict(data=data), broadcast=True, include_self=False)

    @classmethod
    def queue_pop(cls, data):
        return cls._event('queue-pop', dict(data=data), broadcast=True)

    @classmethod
    def queue_status(cls, data):
        return cls._event('queue-status', dict(data=data))

    # -----------------------------------------------------------------------------

    @classmethod
    def event(cls, event, data, **kwargs):
        d = dict(data=data, **kwargs)
        return cls._event(event, d)

    @classmethod
    def _event(cls, event, data, **kwargs):
        logger.debug('>>> {}', event)
        data['event'] = event
        return cls.emit(event, data, **kwargs)

    @classmethod
    def error(cls, message, details=None):
        return cls.emit('fatal-error', dict(event='fatal-error', error=FatalException(message, details)))

    @classmethod
    def exception(cls, ex):
        if isinstance(ex, FatalException):
            return cls.emit('fatal-error', dict(event='fatal-error', error=ex))
        elif isinstance(ex, CompileException):
            return cls.emit('fatal-error', dict(event='fatal-error', error=ex))
        elif isinstance(ex, Exception):
            details = traceback.format_exc().splitlines()
            return cls.error(str(ex), details)
        else:
            return cls.error(str(ex))

    @classmethod
    def emit(cls, *args, **kwargs):
        emit(*args, **kwargs)
        time.sleep(0.1)

