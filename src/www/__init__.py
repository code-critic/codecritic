#!/bin/python3
# author: Jan Hybs

import enum
import pathlib

from bson import objectid
from flask import Flask, redirect, session, render_template, url_for
import flask.json
from flask_cors import CORS
from loguru import logger

from entities.crates import ICrate
from env import Env
from functools import wraps


def default(obj):
    return CustomJSONEncoder().default(obj)


class CustomJSONEncoder(flask.json.JSONEncoder):
    def default(self, obj):
        try:
            from processing import ExecutorStatus

            if isinstance(obj, ExecutorStatus):
                return obj.str

            if isinstance(obj, enum.Enum):
                return obj.value

            if isinstance(obj, (pathlib.Path, pathlib.PosixPath)):
                return str(obj)

            if isinstance(obj, objectid.ObjectId):
                return str(obj)

            if isinstance(obj, ICrate):
                return obj.peek()

            if hasattr(obj, 'peek'):
                return obj.peek()

            return flask.json.JSONEncoder.default(self, obj)
        except:
            logger.exception('encoder error')
            return {}



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if Env.backdoor:
                logger.info('using backdoor for login')
                return redirect(url_for('backdoor_login', id='root', role='root'))
            else:
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


def render_template_base(**kwargs):
    def render(template, **kw):
        kw2 = kwargs.copy()
        kw2.update(kw)
        return render_template(template, **kw2)
    return render


render_template_ext = render_template_base(Env=Env, version=Env.version)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.root_path = Env.www
app.json_encoder = CustomJSONEncoder
cors = CORS(app)


# @app.context_processor
# def override_url_for():
#     """
#     Generate a new token on every request to prevent the browser from
#     caching static files.
#     """
#     return dict(url_for=dated_url_for)
#
#
# def dated_url_for(endpoint, **values):
#     if endpoint == 'static':
#         filename = values.get('filename', None)
#         if filename:
#             file_path = os.path.join(app.root_path, endpoint, filename)
#             values['q'] = int(os.stat(file_path).st_mtime)
#     return url_for(endpoint, **values)
