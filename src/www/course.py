#!/bin/python3
# author: Jan Hybs

from flask import session, url_for
from database.objects import Course, Courses, Languages, User
from www import app, login_required, admin_required, dump_error, render_template_ext
from www.utils_www import Link


def register_routes(app, socketio):
    @app.route('/submit/<string:course_name>/<string:course_year>')
    @login_required
    @dump_error
    def view_course(course_name, course_year):
        user = User(session['user'])
        course = Courses().find_one(name=course_name, year=course_year, only_active=False)
        problems = list(course.problem_db.find(disabled=(None, False)))
        languages = Languages.db().find(disabled=(None, False))

        return render_template_ext(
            'socket.njk',
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
