#!/bin/python3
# author: Jan Hybs

from uuid import uuid4

from flask import redirect, request, session, url_for
from loguru import logger

from database.objects import Courses, Languages, User
from www import admin_required, dump_error, login_required, render_template_ext
from www.utils_www import Link


def register_routes(app, socketio):
    @app.route('/process/<string:course_name>/<string:course_year>', methods=['POST'])
    @login_required
    @dump_error
    def process_solution(course_name, course_year):
        try:
            course = Courses().find_one(name=course_name, year=course_year, only_active=False)
            problem = course.problem_db[request.form['prob-id']]
            lang = Languages.db()[request.form['lang-id']]
            src = request.form['src']
            use_docker = request.form.get('use-docker', 'off') == 'on'
            uuid = uuid4().hex

            session[uuid] = dict(
                problem_id=problem.id,
                lang_id=lang.id,
                course_id=course.id,
                use_docker=use_docker,
                src=src,
                action='solve',
            )

            return redirect(url_for('view_result', uuid=uuid))

        except:
            logger.exception('Could not parse data')

    @app.route('/results/<string:uuid>')
    @login_required
    @dump_error
    def view_result(uuid=None):

        user = User(session['user'])
        results = list()

        if uuid:
            solution = session[uuid]
            course = Courses()[solution['course_id']]
            results.append(dict(
                course=Courses()[solution['course_id']],
                problem=course.problem_db[solution['problem_id']],
                lang=Languages.db()[solution['lang_id']],
                src=solution['src'],
                use_docker=solution['use_docker'],
                live=True,
                uuid=uuid,
            ))

        return render_template_ext(
            'results.njk',
            user=user,
            results=results,

            title='Results',
            subtitle=user.name,
            back=Link(url_for('view_courses'), 'course selection'),
        )

    @app.route('/course/<string:course_name>/<string:course_year>')
    @login_required
    @dump_error
    def view_course(course_name, course_year):
        user = User(session['user'])
        course = Courses().find_one(name=course_name, year=course_year, only_active=False)
        problems = list(course.problem_db.find(disabled=(None, False)))
        languages = Languages.db().find(disabled=(None, False))

        return render_template_ext(
            'submit.njk',
            user=user,
            course=course,
            languages=languages,
            problems=problems,

            title=course.name,
            subtitle=course.year,
            back=Link(url_for('view_courses'), 'course selection'),
        )

    @app.route('/admin/<string:course_name>/<string:course_year>/<string:problem_id>')
    @login_required
    @admin_required
    @dump_error
    def admin_problem(course_name, course_year, problem_id):
        user = User(session['user'])
        course = Courses().find_one(name=course_name, year=course_year, only_active=False)
        problem = course.problem_db[problem_id]
        languages = Languages.db().find(disabled=(None, False))

        return render_template_ext(
            'problem.njk',
            user=user,
            course=course,
            languages=languages,
            problem=problem,

            title='Manage %s' % course.name,
            subtitle=problem.name,
            back=Link(url_for('view_course', course_name=course_name, course_year=course_year), 'problem selection'),
        )

    @app.route('/courses')
    @login_required
    @dump_error
    def view_courses():
        user = User(session['user'])

        courses = list(Courses().find(
            only_active=not user.is_admin()
        ))

        return render_template_ext(
            'courses.njk',
            title='Course list',
            user=user,
            courses=courses
        )
