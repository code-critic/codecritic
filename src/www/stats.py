#!/bin/python3
# author: Jan Hybs
import time
import datetime
from copy import deepcopy

import flask.json
import markdown
from bson import ObjectId
from flask import request, session
from loguru import logger

from database.mongo import Mongo
from database.objects import User
from env import Env
from www import login_required

SKIP = object()


def skip_if_all(x):
    return SKIP if x == 'all' else x


def register_routes(app, socketio):
    @app.route('/api/stats', methods=['POST'])
    def stats():
        data = request.json
        filters = {}

        def add_filter(n, v=None, l=None):
            r = data
            if n.find('.') != -1:
                r, n = data['filters'], n.split('.')[1]

            if r.get(n, None):
                val = l(r.get(n)) if l else r.get(n)
                if val is not SKIP:
                    filters[v or n] = val

        def dummy_object_id(period):
            if period == 'day':
                gen_time = datetime.datetime.today() - datetime.timedelta(days=1)
            elif period == 'week':
                gen_time = datetime.datetime.today() - datetime.timedelta(days=7)
            elif period == 'two weeks':
                gen_time = datetime.datetime.today() - datetime.timedelta(days=14)
            elif period == 'month':
                gen_time = datetime.datetime.today() - datetime.timedelta(days=31)
            else:
                gen_time = datetime.datetime.today() - datetime.timedelta(days=365)
            return ObjectId.from_datetime(gen_time)

        # {'course': 'TST-2019', 'problem': 'problem-1', 'filters':
        #   {'daterange': 'week', 'status': 'all', 'limit-per-user': '3', 'has-review-flag': 'no', 'search': 'a'}}
        limit_per_user = data['filters']['limit-per-user']
        if limit_per_user == 'all':
            limit_per_user = 1000
        else:
            limit_per_user = int(limit_per_user)

        has_review_flag = data['filters']['has-review-flag']
        if has_review_flag == 'yes':
            filters['review_request'] = {'$ne': None}
        if has_review_flag == 'no':
            filters['review_request'] = {'$exists': False}

        sort_by_inner = data['filters']['sort-by-inner']
        sort_by_outer = data['filters']['sort-by-outer']

        add_filter('course')
        add_filter('filters.problem', 'problem', skip_if_all)
        # add_filter('filters.course', 'course', skip_if_all)

        add_filter('filters.status', 'result.status', skip_if_all)
        add_filter('filters.daterange', '_id', lambda x: {'$gte': dummy_object_id(x)})
        base_properties = {x: 1 for x in Mongo().base_properties}

        pipeline = [
            {'$match': filters},
            {'$project': {
                'has_comments': {'$ne': ['$review', None]},
                **base_properties}
            },
            {'$sort': {sort_by_inner: -1}},
            {'$group': {
                '_id': '$user',
                'results': {'$push': '$$ROOT'}  # $$ROOT
            }},
            {'$sort': {sort_by_outer: -1}},
        ]
        print(pipeline, limit_per_user)
        items = list(Mongo().data.aggregate(pipeline))

        result = list()
        for item in items:
            item_copy = deepcopy(item)
            item_copy['results'] = item_copy['results'][0:limit_per_user]
            for attempt in item_copy['results']:
                attempt['time'] = datetime.datetime.timestamp(attempt['_id'].generation_time)
            # item_copy['results'] = sorted(item_copy['results'], key=lambda x: x['time'], reverse=True)
            result.append(item_copy)

        return flask.json.dumps(result)

    @app.route('/api/result/<string:_id>')
    def get_db_result(_id):
        user = User(session['user'])
        result = Mongo().result_by_id(_id)
        output_dir = result.output_dir
        review = result.review

        if output_dir:
            for case in result.results:
                try:
                    case_config = result.ref_problem[case['id']]
                    if case_config:
                        case['attachments'] = case_config.get_attachments(
                            user_dir=Env.root.joinpath(output_dir)
                        )
                except AttributeError:
                    logger.exception('attachments')
                    pass
        if review:
            for line, comments in review.items():
                for i, c in enumerate(comments):
                    comments[i]['text'] = markdown.markdown(c['text'])

        mark_as_read = Mongo().mark_as_read(to=user.id, _id=_id, event='new-comment')
        logger.info('mark-as-read: {}', mark_as_read)

        return flask.json.dumps(
            result
        )

    @app.route('/api/notifications/list', methods=['POST'])
    @login_required
    def load_notifications():
        user = User(session['user'])
        return flask.json.dumps(dict(
            notifications=Mongo().read_notifications(user.id).peek(),
        ))

    @app.route('/api/codereview/add', methods=['POST'])
    @login_required
    def request_review():
        user = User(session['user'])
        data = request.json
        _id = data['_id']
        document = Mongo().result_by_id(_id)
        from_user = document.user or user.id

        # request_dt = document.review_request  # type: datetime
        # if request_dt:
        #     return flask.json.dumps(
        #         dict(result='warning', message=f'Request was already sent on {request_dt:%Y-%m-%d %H:%M:%S}')
        #     )

        # notify all teachers
        reviewers = list()
        for reviewer in document.ref_course.teachers:
            event_document = {
                'from'       : from_user,
                'to'         : reviewer,
                'course'     : document.course,
                'problem'    : document.problem,
                'document'   : _id,
                'event'      : 'codereview',
                'title'      : f'Code review requested by {from_user}',
                'description': f'Student {from_user} has requested code review for the problem {document.ref_problem.id}'
            }

            if Mongo().add_notification(event_document):
                logger.info(f'add-notification: {event_document}')
                reviewers.append(reviewer)
            else:
                logger.warning(f'notification already exists: {event_document}')

        Mongo().update_fields(_id, review_request=datetime.datetime.now())

        if reviewers:
            return flask.json.dumps(
                dict(result='ok', reviewers=reviewers)
            )
        else:
            return flask.json.dumps(
                dict(result='warning', message='Request was already sent')
            )

    @app.route('/api/comment/add', methods=['POST'])
    @login_required
    def add_comment():
        data = request.json
        user = User(session['user'])
        # course = Courses()[data['course']]
        # problem = course.problem_db[data['problem']]
        # attempt = data['attempt']

        _id = data['_id']
        document = Mongo().result_by_id(_id)
        review = document.review or dict()
        now = time.time()

        from_user = user.id
        author_user = document.user

        for comment in data['comments']:
            line, text = str(comment['line']), comment['comment']
            review_line = review[line] if line in review else list()
            review_line.append(dict(
                user=user.id,
                time=now,
                text=text,
            ))
            review[line] = review_line
        recipients = {from_user, author_user}
        for cmts in review.values():
            for cmt in cmts:
                recipients.add(cmt['user'])

        for recipient in recipients:
            if recipient == from_user:
                logger.info('Not creating notification for self')
            else:
                event_document = {
                    'from'       : from_user,
                    'to'         : recipient,
                    'course'     : document.course,
                    'problem'    : document.problem,
                    'document'   : _id,
                    'event'      : 'new-comment',
                    'title'      : f'New comment from {from_user}',
                    'description': f'{document.ref_problem.id} User {from_user} commented your code in problem '
                }

                if Mongo().add_notification(event_document):
                    logger.info('add-notification: {}', event_document)
                else:
                    logger.warning('notification already exists: {}', event_document)

        mark_as_read = Mongo().mark_as_read(to=user.id, _id=_id, event='codereview')
        logger.info('mark-as-read: {}', mark_as_read)

        update_one = Mongo().update_fields(_id, review=review)
        logger.info('document-updated: {}', update_one)

        return flask.json.dumps(
            dict(result='ok')
        )
