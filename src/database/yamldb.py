#!/bin/python3
# author: Jan Hybs

import copy
import pathlib

import yaml

from env import Env


class YamlDB(object):
    """
    :type _data: list
    """

    def __init__(self, yaml_file):
        self.yaml_file = pathlib.Path(yaml_file)
        self._touch_db()
        self._data = None
        self.save_opts = dict(default_flow_style=False)
        self.load_opts = dict()
        self._cls = None
        self._post_processing = list()
        self._bind = dict()
        self._id_prop = 'id'

    def _finish_document(self, doc):
        result = copy.deepcopy(doc)
        result.update(self._bind)

        for func in self._post_processing:
            result = func(result)

        if self._cls:
            result = self._cls(result)
        return result

    def bind(self, **kwargs):
        self._bind = kwargs

    def set_conversion(self, func):
        self._cls = func

    def add_postprocessing(self, func):
        self._post_processing.append(func)

    def set_id_prop(self, id_prop):
        self._id_prop = id_prop

    def set_opts(self, load_opts=None, save_opts=None):
        if load_opts:
            self.load_opts = load_opts

        if save_opts:
            self.save_opts = save_opts

    def _touch_db(self):
        self.yaml_file.parent.mkdir(parents=True, exist_ok=True)
        self.yaml_file.touch()

    def get(self, item, default=None):
        """
        :rtype: cfg.database.objects.Problem | cfg.database.objects.Course | cfg.database.objects.Languages | cfg.database.objects.User
        """
        for doc in self.find(**{self._id_prop: item}):
            return doc
        return default

    def __getitem__(self, item):
        """
        :rtype: cfg.database.objects.Problem | cfg.database.objects.Course | cfg.database.objects.Languages | cfg.database.objects.User
        """
        for doc in self.find(**{self._id_prop: item}):
            return doc
        raise ValueError('No item "%s" found on %s' % (str(item), str(self)))

    def _load(self, func=yaml.load, **kwargs):
        opts = self.load_opts.copy()
        opts.update(kwargs)
        self._data = func(self.yaml_file.read_text(), **opts) or list()
        return self._data

    def _save(self, func=yaml.dump, **kwargs):
        self._load()
        opts = self.save_opts.copy()
        opts.update(kwargs)
        content = func(self._data, **opts)
        return self.yaml_file.write_text(content)

    def add(self, item):
        self._load()
        self._data.append(item)
        self._save()
        return item

    def find_one(self, **conditions):
        """
        :rtype: cfg.database.objects.Problem | cfg.database.objects.Course | cfg.database.objects.Languages | cfg.database.objects.User
        """
        for item in self.find(**conditions):
            return item
    
    def find(self, **conditions):
        """
        :rtype: typing.List[cfg.database.objects.Problem | cfg.database.objects.Course | cfg.database.objects.Languages | cfg.database.objects.User]
        """
        self._load()
        for item in self._data:
            match = True
            for k, v in conditions.items():
                vv = item.get(k, None)
                if isinstance(v, (list, tuple)):
                    match &= vv in v
                else:
                    match &= vv == v

            if match:
                yield self._finish_document(item)

    def _find(self, **conditions):
        """
        :rtype: typing.List[cfg.database.objects.Problem | cfg.database.objects.Course | cfg.database.objects.Languages | cfg.database.objects.User]
        """
        return list(self.find(**conditions))

    def __repr__(self):
        return '{self.__class__.__name__}({self.yaml_file})'.format(self=self)


class ADB(object):
    storage = None
    id_prop = 'id'
    ignores = list()

    @classmethod
    def db(cls):
        if not hasattr(cls, '__database'):
            cls.__database = YamlDB(pathlib.Path(Env.cfg).joinpath(cls.storage))
            cls.__database.set_id_prop(cls.id_prop)
            cls.__database.set_conversion(cls)
        return cls.__database

    def __repr__(self):
        rest = list()
        for k, v in self.peek().items():
            rest.append('%s=%s' % (str(k), str(v)))
        return '{self.__class__.__name__}({rest})'.format(self=self, rest=', '.join(rest))

    def peek_full(self):
        return self.__dict__

    def peek(self):
        return {k: v for k, v in self.__dict__.items() if k not in self.__class__.ignores and v is not None}

    def _peek(self, *props):
        return {k: getattr(self, k) for k in props if hasattr(self, k)}
