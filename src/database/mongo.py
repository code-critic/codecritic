#!/bin/python3
# author: Jan Hybs

import datetime

import yaml
from loguru import logger

from pymongo import MongoClient
from singleton_decorator import singleton
from env import Env


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

    def save_result(self, result):
        """
        :type result: dict
        """
        try:
            cp = result.copy()
            if cp.get('solution', None):
                cp['solution'] = cp['solution'][0:32].strip() + '...'
            yaml_log = yaml.dump(cp, default_flow_style=False)
            logger.info('logging request result: \n{}', yaml_log)
        except Exception as e:
            logger.exception(e)
            logger.info('logging request result: \n{}', result)

        return self.data.insert_one(result)

    def load_logs(self, *args, **kwargs):
        return self.logs.find(*args, **kwargs)

    def load_results(self, *args, **kwargs):
        return self.data.find(*args, **kwargs)
