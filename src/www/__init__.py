#!/bin/python3
# author: Jan Hybs
import enum
import pathlib

from flask import Flask, redirect, session
import flask.json
from flask_cors import CORS
from flask_socketio import SocketIO
from loguru import logger

from env import Env
from functools import wraps


class CustomJSONEncoder(flask.json.JSONEncoder):
    def default(self, obj):
        from processing import ExecutorStatus

        if isinstance(obj, ExecutorStatus):
            return obj.str

        if isinstance(obj, enum.Enum):
            return obj.value

        if isinstance(obj, pathlib.Path):
            return str(obj)

        if hasattr(obj, 'peek'):
            return obj.peek()

        return flask.json.JSONEncoder.default(self, obj)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(Env.url_login)
        return f(*args, **kwargs)
    return decorated_function


def dump_error(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            import traceback, html
            logger.exception('@dump_error')
            return '<pre>%s</pre>' % html.escape(traceback.format_exc())
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from database.objects import User
        try:
            user = User(session['user'])
            if not user.is_admin():
                raise Exception('Access denied')
        except:
            return redirect(Env.url_login)

        return f(*args, **kwargs)
    return decorated_function


async_mode = 'eventlet'  # eventlet, gevent_uwsgi, gevent, threading
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.root_path = Env.www
app.json_encoder = CustomJSONEncoder
cors = CORS(app)
socketio = SocketIO(app, json=flask.json, async_mode=async_mode)

