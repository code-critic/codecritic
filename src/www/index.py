#!/bin/python3
# author: Jan Hybs

from flask import redirect, url_for
from www import app, login_required


@app.route('/')
@app.route('/index')
@login_required
def index():
    return redirect(url_for('view_courses'))
