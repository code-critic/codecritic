#!/bin/python3
# author: Jan Hybs

import yaml


class Lang(yaml.YAMLObject):
    # register yaml name
    yaml_tag = '!Prob'

    # Here will be the instance stored.
    instances = dict()

    @classmethod
    def read_config(cls, filepath):
        with open(filepath, 'r') as fp:
            items = [cls(y) for y in yaml.load(fp)]

    @classmethod
    def get(cls, lang_id):
        """
        :rtype: Lang
        """
        if lang_id not in cls.instances:
            raise Exception('No such language defined')
        return cls.instances.get(lang_id)

    def __init__(self, conf: dict):
        self.name = conf.get('name')
        self.version = conf.get('version')
        self.id = conf.get('id')
        self.compile = conf.get('compile')  # type: list[str]
        self.execute = conf.get('execute')  # type: list[str]
        self.ext = conf.get('ext', [])

        if self.id in self.__class__.instances:
            raise Exception('Language already defined')

        self.__class__.instances[self.id] = self

    def peek(self):
        return dict(
            id=self.id,
            name=self.name,
            version=self.version
        )

    def __repr__(self):
        return '{self.__class__.__name__}([{self.id}], {self.name}=={self.version})'.format(self=self)
