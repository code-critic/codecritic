#!/bin/python3
# author: Jan Hybs


def register_routes(app, socketio):
    from database.objects import User
    from flask import session, redirect, url_for
    from env import Env

    Env.backdoor = True

    @app.route('/backdoor/<string:id>/<string:role>/')
    @app.route('/backdoor/<string:role>/')
    def backdoor_login(role, id=None):
        session['user'] = User(dict(id=id, role=role, affi='debug'))
        return redirect(url_for('view_courses'))
