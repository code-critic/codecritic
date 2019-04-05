#!/bin/python3
# author: Jan Hybs

from flask import session, redirect
from env import Env
from utils.crypto import SimpleCrypto
from database.objects import User
from www import app, admin_required


@app.route('/login/<string:data>')
def login(data):
    crypto = SimpleCrypto(Env.secret_key())
    json_data = crypto.decrypt_json(data)
    user = User.from_json(json_data)

    try:
        registered = User.db()[user.id]
        if registered:
            user.role = registered.role
    except: pass

    session['user'] = user.peek()

    return redirect('courses')


@app.route('/logout')
def logout():
    del session['user']
    return redirect(Env.url_logout)


@app.route('/admin/switch-role/<string:id>/<string:role>/')
@app.route('/admin/switch-role/<string:role>/')
@admin_required
def admin_switch_role(role, id=None):
    user = User(session['user'])
    session['user'] = User(dict(id=id or user.id, role=role, affi='debug'))
    return redirect('courses')
