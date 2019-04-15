#!/bin/python3
# author: Jan Hybs

import datetime

import yaml
from loguru import logger

from pymongo import MongoClient
from singleton_decorator import singleton
from env import Env
from utils.strings import ensure_iterable


@singleton
class Mongo(object):

    def __init__(self):
        config = Env.database_config()

        self.client = MongoClient(**config['options'])
        self.db = self.client.get_database(**config['database'])

        self.logs = self.db.get_collection(config['collections']['logs'])
        self.data = self.db.get_collection(config['collections']['data'])
        logger.info('Using db {}', self)

    def __repr__(self):
        return ('Mongo({self.client.address[0]}:{self.client.address[1]}'
                '/{self.db.name}/{{{self.logs.name}, {self.data.name}}})').format(self=self)

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

    def save_result(self, result, **extra):
        """
        :type result: dict
        """
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

    def last_n_results_from_students(self, n=100, course_id=None, problem_id=None):
        match = self._fix_dict(dict(course=course_id, problem=problem_id, action='solve'))
        group = dict(
            _id='$user',
            results={'$push': {
                'status': '$result.status',
                'duration': '$result.duration',
                'message': '$result.message',
                'language': '$language',
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

    @staticmethod
    def _fix_dict(d: dict):
        return {k:v for k, v in d.items() if v not in (None, [])}
