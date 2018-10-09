#!/bin/python3
# author: Jan Hybs


import enum
import os
import uuid

import yaml
from cfg.languages import Lang
from cfg.problems import Prob, StaticTest


class Request(yaml.YAMLObject):
    class Action(enum.Enum):
        TEST = 'test'
        GENERATE_OUTPUT = 'generate-output'

    # register yaml name
    yaml_tag = '!Request'

    @classmethod
    def read(cls, filepath):
        with open(filepath, 'r') as fp:
            return cls(yaml.load(fp))

    def __init__(self, conf: dict):
        self.root = conf.get('root')    # type: str
        self.user = conf.get('user')    # type: str
        self.lang = conf.get('lang')    # type: Lang
        self.prob = conf.get('prob')    # type: Prob
        self.file = conf.get('file', 'main.%s' % self.lang.ext[0])    # type: str
        self.resu = '.'.join(self.user.split('.')[::-1])  # type: str
        self.action = Request.Action(conf.get('action', 'test'))
        self.use_docker = conf.get('docker', True)
        self.source_code = conf.get('src', None)
        self.id = conf.get('id', uuid.uuid4().hex)

        self.priority = conf.get('priority', 1)
        self.compare = conf.get('compare', True)
        self.abort_on_error = conf.get('abort-on-error', False)

        self.config = dict(
            filename=self.file,
            filepath=os.path.join(self.root, self.file),
            filename_no_ext='.'.join(self.file.split('.')[:-1]),
            filepath_no_ext=os.path.join(self.root, '.'.join(self.file.split('.')[:-1]))
        )

        tests = conf.get('tests', [x.id for x in self.prob.tests])
        self.tests = [x for x in self.prob.tests if x.id in tests]  # type: list[StaticTest]
        self.running = False

    def peek(self):
        return dict(
            id=self.id,
            root=self.root,
            user=self.user,
            lang=self.lang.peek(),
            prob=self.prob.peek(),
            action=self.action.value,
            running=self.running,
        )

    def __repr__(self):
        return "{self.__class__.__name__}(from '{self.user}' for '{self.prob.id}' via '{self.lang.id}')".format(self=self)
