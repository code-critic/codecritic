#!/bin/python3
# author: Jan Hybs

import sys
from flask import redirect, url_for, send_file

from database.objects import User, Courses
from env import Env
from www import login_required, render_template_ext, session
from loguru import logger
from utils.crypto import b64decode
from www.utils_www import Link


max_file_view_limit = 1024*1024


def register_routes(app, socketio):
    @app.route('/')
    @app.route('/index')
    @login_required
    def index():
        return redirect(url_for('view_courses'))

    @app.route('/index2')
    @login_required
    def index2():
        user = User(session['user'])

        courses = list(Courses().find(
            only_active=not user.is_admin()
        ))

        return render_template_ext(
            'new.njk',
            title='Courses',
            courses=courses,
            user=user,
            back=Link(url_for('view_courses'), 'course selection'),
        )

    @app.route('/log')
    def print_log():
        log = Env.log_file.read_text()
        import ansi2html

        converter = ansi2html.Ansi2HTMLConverter()
        html = converter.convert(log)
        return '<h1>Automate log</h1>' + html

    @app.route('/log/clear')
    @login_required
    def clear_log():
        Env.log_file.unlink()
        Env.log_file.touch()

        logger.configure(handlers=[
            dict(sink=sys.stdout),
            dict(sink=Env.log_file, colorize=True)
        ])

        logger.info('--- log file cleared ---')
        return redirect('/log')

    @app.route('/file/<string:data>/<string:as_name>')
    def serve_file(data: str, as_name: str):
        result = b64decode(data)
        local = Env.root.joinpath(*result['url'])
        assert local.parts[-2] in ('input', 'output', '.error')
        if local.exists():
            if local.stat().st_size > max_file_view_limit:
                return send_file(str(local), mimetype='text/plain', as_attachment=True, attachment_filename=as_name)
            else:
                return send_file(str(local), mimetype='text/plain', attachment_filename=as_name)
        return 'File not found'
        # return send_file(str(local), mimetype='text/plain', as_attachment=True, attachment_filename=as_name)
