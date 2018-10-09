#!/bin/python3
# author: Jan Hybs
from collections import defaultdict, OrderedDict

import time
import yaml
import os
import markdown
import glob
import re
import datetime as dt

from cfg.env import variables as env
from stats.highcharts import generate_pie_code
from utils.io import read_file

def parse_dt(d):
    if d is None:
        return None
    if type(d) is dt.datetime:
        return d
    return dt.datetime(*list(map(int, re.split("[\D]+", d.strip()))))

class Prob(yaml.YAMLObject):
    # register yaml name
    yaml_tag = '!Prob'

    # Here will be the instance stored.
    instances = OrderedDict()   # type: dict[str, Prob]

    @classmethod
    def read_config(cls, filepath):
        with open(filepath, 'r') as fp:
            items = [cls(y) for y in yaml.load(fp)]

    @classmethod
    def groups(cls):
        result = OrderedDict()
        for test_id, test in cls.instances.items():
            if test.group not in result:
                result[test.group] = OrderedDict()
            result[test.group][test_id] = test
        return result

    @classmethod
    def get(cls, prob_id):
        """
        :rtype: Prob
        """
        if prob_id not in cls.instances:
            raise Exception('No such problem defined')
        return cls.instances.get(prob_id)

    def __init__(self, conf: dict):
        # print(conf)
        self.name = conf.get('name')
        self.id = conf.get('id')
        self.tests = conf.get('tests')  # type: list[StaticTest]
        desc = os.path.join(env.data, self.id, 'README.md')
        self.description = markdown.markdown(read_file(desc))
        self.group = conf.get('group', '')
        self.enabled = conf.get('enabled', True)
        self.avail = parse_dt(conf.get('avail', None))

        if self.id in self.__class__.instances:
            raise Exception('Problem already defined')

        for test in self.tests:
            test.locate(self)

        self.__class__.instances[self.id] = self
        self._stats = dict()
        self._last_update = 0
        self._update_period = 60*5

    def peek(self):
        return dict(
            id=self.id,
            name=self.name,
            tests=[x.peek() for x in self.tests]
        )

    def is_active(self):
        return self.enabled and self.time_left > 0

    @property
    def time_left(self):
        if not self.avail:
            return 10**10
        return int((self.avail - dt.datetime.now()).total_seconds())

    @property
    def html_disabled(self):
        return '' if self.is_active() else 'disabled'

    def stats(self, group='*'):
        now = time.time()
        if (now - self._last_update) > self._update_period:
            self._stats = dict()

        if not self._stats:
            self._last_update = now
            path = '%s/*/%s/*/result.yaml' % (env.results, self.id)
            results = defaultdict(lambda: defaultdict(lambda: 0))

            for filename in glob.glob(path, recursive=True):
                with open(filename, 'r') as fp:
                    data = yaml.load(fp)
                    if data and 'tests' in data:
                        for test in data['tests']:
                            results[test['id']][test['result']] += 1
                        # results['*'][data['result']] += 1

            # self._stats = {k: generate_pie_code(results[k]) for k in results}
            self._stats = generate_pie_code(results)

        return self._stats

    def __repr__(self):
        return '{self.__class__.__name__}([{self.id}] {self.name}, t:{self.tests})'.format(self=self)


class StaticTest(yaml.YAMLObject):
    # register yaml name
    yaml_tag = '!StaticTest'

    def __setstate__(self, state):
        self.__init__(**state)

    def __init__(self, id, time):
        self.id = id        # type: str
        self.time = time    # type: float
        self.prob = None    # type: Prob
        self.input = None   # type: str
        self.output = None  # type: str
        self.error = None   # type: str

    def locate(self, prob: Prob):
        self.prob = prob
        self.input = os.path.join(env.data, prob.id, 'input', self.id)
        self.output = os.path.join(env.data, prob.id, 'output', self.id)

        os.makedirs(os.path.join(env.data, prob.id, 'input'), exist_ok=True)
        os.makedirs(os.path.join(env.data, prob.id, 'output'), exist_ok=True)

    def peek(self):
        return dict(
            id=self.id,
            time=self.time,
        )

    def __repr__(self):
        return '{self.__class__.__name__}([{self.id}] <{self.time})'.format(self=self)
