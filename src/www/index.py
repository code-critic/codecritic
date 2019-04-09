#!/bin/python3
# author: Jan Hybs

import html
from flask import redirect, url_for
from env import Env
from www import app, login_required


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
