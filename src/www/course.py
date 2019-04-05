#!/bin/python3
# author: Jan Hybs

from flask import render_template, session, url_for
from database.objects import Course, Languages, User
from www import app, login_required, admin_required
from www.utils_www import Link


@app.route('/submit/<string:course_name>/<string:course_year>')
@login_required
def view_course(course_name, course_year):
    user = User(session['user'])
    course = Course.db().find_one(name=course_name, year=course_year)
    problems = list(course.problem_db.find(disabled=(None, False)))
    languages = Languages.db().find(disabled=(None, False))

    return render_template(
        'socket.njk',
        user=user,
        course=course,
        languages=languages,
        problems=problems,

        title=course.name,
        subtitle=course.year,
        back=Link(url_for('view_courses'), 'go back'),
    )


@app.route('/admin/<string:course_name>/<string:course_year>/<string:problem_id>')
@login_required
@admin_required
def admin_problem(course_name, course_year, problem_id):
    user = User(session['user'])
    course = Course.db().find_one(name=course_name, year=course_year)
    problem = course.problem_db[problem_id]
    languages = Languages.db().find(disabled=(None, False))

    return render_template(
        'problem.njk',
        user=user,
        course=course,
        languages=languages,
        problem=problem,

        title='Manage %s' % course.name,
        subtitle=problem.name,
        back=Link(url_for('view_course', course_name=course_name, course_year=course_year), 'go back'),
    )


@app.route('/courses')
@login_required
def view_courses():
    user = User(session['user'])
    filters = dict() if user.is_admin() else dict(disabled=(None, False))
    courses = [course for course in Course.db().find(**filters) if user.in_course(course)]

    return render_template(
        'courses.njk',
        title='Course list',
        user=user,
        courses=courses
    )
