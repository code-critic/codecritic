#!/bin/python3
# author: Jan Hybs

import html, sys
from flask import redirect, url_for, send_file
from env import Env
from www import app, login_required
from loguru import logger
from utils.crypto import b64decode

@app.route('/')
@app.route('/index')
@login_required
def index():
    return redirect(url_for('view_courses'))


@app.route('/log')
def print_log():
    log = Env.log_file.read_text()

    return '''
    <h1>Automate log</h1>
    <pre>%s</pre>
    '''.strip() % html.escape(log)

@app.route('/log/clear')
def clear_log():
    Env.log_file.unlink()
    Env.log_file.touch()

    logger.configure(handlers=[
        dict(sink=sys.stdout),
        dict(sink=Env.log_file)
    ])

    logger.info('--- log file cleared ---')
    return redirect('/log')


@app.route('/file/<string:data>/<string:as_name>')
def serve_file(data: str, as_name: str):
    result = b64decode(data)
    local = Env.root.joinpath(*result['url'])
    assert local.parts[-2] in ('input', 'output', '.error')
    return send_file(str(local), mimetype='text/plain', attachment_filename=as_name)
    # return send_file(str(local), mimetype='text/plain', as_attachment=True, attachment_filename=as_name)
