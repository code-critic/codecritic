#!/bin/python3
# author: Jan Hybs
import datetime
import time

import yaml
from bson import objectid
from bson.errors import InvalidId
from loguru import logger
from pymongo import MongoClient
from singleton_decorator import singleton

from database.objects import Notifications
from entities.crates import ICrate
from env import Env
from utils.strings import ensure_iterable
from utils.types import ensure_type


SINCE_EPOCH = datetime.datetime.fromtimestamp(0)

@singleton
class Mongo(object):

    base_properties = [
        '_id',
        'user',
        'attempt',
        'course',
        'problem',
        'lang',
        'result.status',
        'result.duration',
        'result.score',
        'result.scores',
        'review_request',
    ]

    def __init__(self):
        config = Env.database_config()

        self.client = MongoClient(**config['options'])
        self.db = self.client.get_database(**config['database'])

        self.logs = self.db.get_collection(config['collections']['logs'])
        self.data = self.db.get_collection(config['collections']['data'])
        self.events = self.db.get_collection(config['collections']['events'])
        logger.info('Using db {}', self)

    def __repr__(self):
        return ('Mongo({self.client.address[0]}:{self.client.address[1]}'
                '/{self.db.name}/{{{self.logs.name}, {self.data.name}, {self.events.name}}})').format(self=self)

    def save_log(self, log):
        """
        :type log: dict
        """
        try:
            cp = log.copy()
            cp['solution'] = cp.get('solution', '')[0:32].strip() + '...'
            yaml_log = yaml.dump(cp, default_flow_style=False)
            logger.info('logging new request: \n{}', yaml_log)
        except Exception as e:
            logger.exception(e)
            logger.info('logging new request: \n{}', log)

        return self.logs.insert_one(log)

    def save_result(self, result, _id=None, **extra):
        """
        :type result: dict
        """
        if isinstance(result, ICrate):
            result = result.peek()

        _id: objectid.ObjectId = ensure_type(_id, objectid.ObjectId)

        try:
            cp = result.copy()
            cp.update(extra)

            if cp.get('solution', None):
                cp['solution'] = cp['solution'][0:32].strip() + '...'

            yaml_log = yaml.dump(cp, default_flow_style=False)
            logger.info('logging request result: \n{}', yaml_log)
        except Exception as e:
            logger.exception(e)
            logger.info('logging request result: \n{}', result)

        result.update(extra)
        if _id:
            result['_id'] = _id
            return self.data.replace_one(dict(_id=result['_id']), result)

        if '_id' in result:
            del result['_id']
        return self.data.insert_one(result)

    def load_logs(self, *args, **kwargs):
        return self.logs.find(*args, **kwargs)

    def last_n_correct_results(self, n=10, user_id=None, course_id=None, problem_id=None):
        return self.last_n_results(n, user_id, course_id, problem_id, statuses='answer-correct')

    def last_n_wrong_results(self, n=10, user_id=None, course_id=None, problem_id=None):
        return self.last_n_results(n, user_id, course_id, problem_id, statuses='answer-correct', status_op='$nin')

    def last_n_results(self, n=10, user_id=None, course_id=None, problem_id=None, statuses=None, status_op='$in'):
        filters = self._fix_dict(dict(user=user_id, course=course_id, problem=problem_id))

        statuses = ensure_iterable(statuses)
        if statuses:
            filters['result.status'] = {status_op: statuses}

        logger.info('Fetching db documents using filter {}', filters)
        cursor = self.data.find(filters).sort('_id', -1).limit(n)

        return cursor

    def peek_last_n_results(self, n=10, user_id=None, course_id=None, problem_id=None, statuses=None, status_op='$in'):
        from entities.crates import TestResult
        filters = self._fix_dict(dict(user=user_id, course=course_id, problem=problem_id))
        filters['action'] = 'solve'

        statuses = ensure_iterable(statuses)
        if statuses:
            filters['result.status'] = {status_op: statuses}

        logger.info('Fetching db documents using filter {}', filters)
        cursor = self.data.find(
            filters, {x: 1 for x in self.base_properties}
        ).sort('_id', -1).limit(n)

        return [TestResult(**x) for x in cursor]

    def result_by_id(self, _id):
        from entities.crates import TestResult
        try:
            result = self.data.find_one(dict(_id=objectid.ObjectId(_id)))
        except InvalidId:
            return None

        if result:
            return TestResult(**result)
        return None

    def update_fields(self, _id, **fields):
        return self.data.update_one(
            filter=dict(_id=objectid.ObjectId(_id)),
            update={
                '$set': fields
            }
        )

    def last_n_results_from_students(self, n=100, course_id=None, problem_id=None):
        match = self._fix_dict(dict(course=course_id, problem=problem_id, action='solve'))
        group = dict(
            _id='$user',
            results={'$push': {
                'status'    : '$result.status',
                'duration'  : '$result.duration',
                'message'   : '$result.message',
                'language'  : '$language',
                'output_dir': '$output_dir',
                # 'solution': 'solution',
            }},
        )
        pipeline = [
            {'$match': match},
            {'$sort': {'_id': -1}},
            {'$limit': n},
            {'$group': group},
        ]
        logger.info('Fetching db documents using pipeline {}', pipeline)
        return self.data.aggregate(pipeline)

    def load_results(self, *args, **kwargs):
        return self.data.find(*args, **kwargs)

    def read_notifications(self, user_id, course_id=None, problem_id=None):
        filters = dict(to=user_id)
        if course_id:
            filters['course'] = course_id
        if problem_id:
            filters['problem'] = problem_id

        result = list(self.events.find(filters))
        return Notifications(*result)

    def add_notification(self, data):
        id = {'from': data['from'], 'to': data['to'], 'document': data['document']}
        if self.events.find_one(id) is None:
            data['time'] = time.time()
            return self.events.insert_one(data).acknowledged
        return False

    def mark_as_read(self, to, _id, event):
        """
        Will remove notifications where recipient is to and document is _id
        :param to:
        :param _id:
        :return:
        """
        if to:
            return self.events.delete_many(dict(to=to, document=_id, event=event))
        else:
            return self.events.delete_many(dict(document=_id, event=event))

    @staticmethod
    def _fix_dict(d: dict):
        return {k: v for k, v in d.items() if v not in (None, [])}
