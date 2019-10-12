#!/bin/python3
# author: Jan Hybs

from uuid import uuid4
from itertools import groupby
from collections import OrderedDict

from typing import List
from flask import redirect, request, session, url_for
from loguru import logger

from database.mongo import Mongo
from database.objects import Courses, Languages, User, Problem
from env import Env
from www import admin_required, dump_error, login_required, render_template_ext
from www.utils_www import Link, Breadcrumbs
from entities import crates

problem_cat_getter = lambda x: x.cat


def register_routes(app, socketio):
    @app.route('/process/<string:course_name>/<string:course_year>', methods=['POST'])
    @login_required
    @dump_error
    def process_solution(course_name, course_year):
        user = User(session['user'])

        try:
            course = Courses().find_one(name=course_name, year=course_year, only_active=False)
            problem = course.problem_db[request.form['prob-id']]
            lang = Languages.db()[request.form['lang-id']]
            solution = request.form['src']
            use_docker = request.form.get('use-docker', 'off') == 'on'

            test_result = crates.TestResult(
                user=user.id,
                problem=problem.id,
                lang=lang.id,
                course=course.id,
                docker=use_docker,
                solution=solution,
                action='solve',
            )
            # save to the db and redirect with _id
            insert_result = Mongo().save_result(test_result.peek())

            return redirect(
                url_for(
                    'view_result',
                    course_name=course.name,
                    course_year=course.year,
                    problem_id=problem.id,
                    _id=str(insert_result.inserted_id)
                )
            )

        except:
            logger.exception('Could not parse data')

    @app.route('/r/<string:_id>')
    @login_required
    @dump_error
    def perma_result(_id):
        user = User(session['user'])
        document = Mongo().result_by_id(_id)
        course = document.ref_course
        problem = document.ref_problem
        breadcrumbs = [Link.CoursesBtn(), Link.CourseBtn(course), Link.ProblemBtn(course, problem)]

        return render_template_ext(
            'view_result.njk',
            user=user,
            notifications=Mongo().load_notifications(user.id),
            results=[document],
            result=None,
            requestReview=False,

            title='Problem %s' % problem.name,
            breadcrumbs=Breadcrumbs.new(*breadcrumbs),
            js=[
                '//cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.6/highlight.min.js',
                '/static/js/lib/highlightjs-line-numbers.js'
            ],
            js_no_cache=['sockets.js', 'process.js']
        )

    @app.route('/results/<string:course_name>/<string:course_year>/<string:problem_id>/<string:_id>')
    @app.route('/results/<string:course_name>/<string:course_year>/<string:problem_id>')
    @login_required
    @dump_error
    def view_result(course_name, course_year, problem_id, _id=None):
        user = User(session['user'])

        if user.is_admin():
            return redirect(
                url_for('admin_problem', course_name=course_name, course_year=course_year, problem_id=problem_id)
            )

        course = Courses().find_one(name=course_name, year=course_year, only_active=False)
        problem = course.problem_db[problem_id]
        results = list()
        result = None
        breadcrumbs = [Link.CoursesBtn(), Link.CourseBtn(course)]

        # TODO check access
        if _id:
            document = Mongo().result_by_id(_id)
            if document:
                # add to previous solution if already executed
                if document.result:
                    results.append(document)
                else:
                    result = document
                    breadcrumbs.append(
                        Link.ProblemBtn(course, problem)
                    )

        if Env.use_database:
            for prev in Mongo().peek_last_n_results(10, user.id, course.id, problem.id):
                # push only valid result
                if prev.result and str(prev._id) != str(_id):
                    results.append(prev)

        if _id:
            for r in results:
                if str(r._id) == str(_id):
                    r.active = 'active'

        def get_attempt(obj):
            try:
                return int(obj.attempt)
            except:
                return 0

        results = sorted(results, reverse=True, key=get_attempt)

        return render_template_ext(
            'view_result.njk',
            user=user,
            notifications=Mongo().load_notifications(user.id),
            results=results,
            result=result,
            requestReview=True,

            title='Problem %s' % problem.name,
            breadcrumbs=Breadcrumbs.new(*breadcrumbs),
            js=[
                '//cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.6/highlight.min.js',
                '/static/js/lib/highlightjs-line-numbers.js'
            ],
            js_no_cache=['sockets.js', 'process.js']
        )

    @app.route('/course/<string:course_name>/<string:course_year>')
    @login_required
    @dump_error
    def view_course(course_name, course_year):
        user = User(session['user'])
        course = Courses().find_one(name=course_name, year=course_year, only_active=False)
        problems: List[Problem] = sorted(
            list(course.problem_db.find(disabled=(None, False))),
            key=problem_cat_getter
        )

        languages = Languages.db().find(disabled=(None, False))

        if not user.is_admin():
            problems = [p for p in problems if p.is_visible()]

        cat_problems = OrderedDict()
        for cat, items in groupby(problems, key=problem_cat_getter):
            cat_problems[cat] = list(items)

        return render_template_ext(
            'view_course.njk',
            user=user,
            notifications=Mongo().load_notifications(user.id),
            course=course,
            languages=languages,
            has_categories=len(cat_problems) > 1,
            problems=problems,
            cat_problems=cat_problems,

            title=course.name,
            subtitle=course.year,
            breadcrumbs=Breadcrumbs.new(
                Link.CoursesBtn(),
            ),
            js_no_cache=['solution.js']
        )

    @app.route('/admin/<string:course_name>/<string:course_year>/<string:problem_id>')
    @login_required
    @admin_required
    @dump_error
    def admin_problem(course_name, course_year, problem_id):
        user = User(session['user'])
        course = Courses().find_one(name=course_name, year=course_year, only_active=False)
        problems_ids = ','.join([x.id for x in list(course.problem_db.find())])
        problem = course.problem_db[problem_id]
        languages = Languages.db().find(disabled=(None, False))

        return render_template_ext(
            'admin_problem.njk',
            user=user,
            notifications=Mongo().load_notifications(user.id),
            course=course,
            languages=languages,
            problem=problem,
            problems_ids=problems_ids,

            title='Manage problem %s' % problem.name,
            breadcrumbs=Breadcrumbs.new(
                Link.CoursesBtn(),
                Link.CourseBtn(course)
            ),
            js_no_cache=['sockets.js', 'manage-problem.js']
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
            'view_courses.njk',
            title='Course list',
            user=user,
            notifications=Mongo().load_notifications(user.id),
            courses=courses
        )
