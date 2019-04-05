#!/bin/python3
# author: Jan Hybs
import pathlib

import typing
import datetime as dt
import os

from database import parse_dt
from database.yamldb import ADB, YamlDB

from utils import strings
from env import Env


class User(ADB):
    """
    :type id: str
    :type name: str
    :type role: str
    :type affi: str
    :type email: str
    """
    storage = 'users.yaml'

    def __init__(self, item: dict):
        self.id = item['id']
        self.di = '.'.join(self.id.split('.')[::-1])
        self.name = item.get('fullname', ' '.join([x.capitalize() for x in self.id.split('.')]))
        self.email = item.get('email')
        self.role = item.get('role')
        self.affi = item.get('affi')

        parts = self.id.split('.')
        if len(parts) == 2:
            self.first_name, self.last_name = parts
        else:
            self.first_name, self.last_name = '', '.'.join(parts)

    def is_admin(self):
        return self.role in ('root', 'admin')

    def in_course(self, course):
        """
        :param course: Course
        """
        if course.students:
            if self.id in course.students:
                return True

        if course.teachers:
            if self.id in course.teachers:
                return True

        return self.is_admin()

    @classmethod
    def from_json(cls, user):
        email = user['eppn']
        id = user['eppn'].split('@')[0]
        affi = ', '.join(user['affiliation'].lower().replace('@tul.cz', '').split(';'))

        return cls(dict(id=id, affi=affi, email=email))

    @property
    def affi_pairs(self):
        items = self.affi.split(', ') if self.affi else list()
        for i in range(0, len(items), 3):
            yield ', '.join(items[i:i+3])

class Course(ADB):
    """
    :type name: str
    :type desc: str
    :type year: str
    :type disabled: bool
    :type teachers: list[str]
    :type students: list[str]
    """
    storage = 'courses.yaml'
    _problems = dict()

    def __init__(self, item: dict):
        super().__init__()
        self.id = item['id']
        self.name = item.get('name')
        self.desc = item.get('desc')
        self.year = item.get('year')
        self.disabled = item.get('disabled', False)
        self.teachers = item.get('teachers', list())
        self.students = item.get('students', list())

        if self.year:
            self.yaml_file = pathlib.Path(Env.cfg).joinpath(str(self.year).lower(), self.name.lower() + '.yaml')
        else:
            self.yaml_file = pathlib.Path(Env.cfg).joinpath(self.name.lower() + '.yaml')

    def peek(self):
        return self._peek('id', 'name', 'desc', 'year', 'enabled')

    @property
    def problem_db(self):
        """
        :rtype: YamlDB
        """
        if self.id not in self._problems:
            db = YamlDB(self.yaml_file)
            db.set_conversion(Problem)
            db.bind(course_id=self.id)
            self._problems[self.id] = db
        return self._problems[self.id]


class Languages(ADB):
    """
    :type id: str
    :type name: str
    :type extension: str
    :type version: str
    :type compile: list[str]
    :type run: list[str]
    :type scale: float
    :type style: str
    """
    storage = 'langs.yaml'

    def __init__(self, item: dict):
        super().__init__()
        self.id = item['id']
        self.name = item.get('name')
        self.extension = item.get('extension')
        self.version = item.get('version')
        self.compile = strings.ensure_iterable(item.get('compile', list()))
        self.run = strings.ensure_iterable(item.get('run', list()))
        self.scale = item.get('scale', 1.0)
        self.image = item.get('image')
        self.disabled = item.get('disabled', False)
        self.style = item.get('style')

    def __bool__(self):
        return not self.disabled

    def peek(self):
        return self._peek('id', 'name', 'extension')

    @property
    def pretty_name(self):
        if self.version:
            return '{self.name} ({self.version})'.format(self=self)
        return self.name


class Script(object):
    """
    :type name: str
    :type lang: str
    """
    def __init__(self, item: dict):
        super().__init__()
        self.name = item['name']
        self.lang = item['lang']

    @property
    def lang_ref(self):
        """
        :rtype: Languages
        """
        return Languages.db().get(self.lang)

    def peek(self):
        return str(self)

    def __repr__(self):
        return 'Script(name={self.name}, lang={self.lang})'.format(self=self)


class Problem(ADB):
    """
    :type id: str
    :type id: str
    :type desc: str
    :type tests: list[ProblemCase]
    :type reference: Script
    """

    def __init__(self, item: dict):
        super().__init__()
        self.id = item['id']
        self.name = item.get('name')
        self.desc = item.get('desc')
        self.reference = Script(item.get('reference')) if item.get('reference') else None
        self.disabled = item.get('disabled', False)
        self.avail = parse_dt(item.get('avail'))
        self.course_id = item.get('course_id')
        self.timeout = item.get('timeout')
        self.tests = list()

        for test in item.get('tests', list()):
            self.tests.append(ProblemCase(test, self))

    def peek(self):
        return self._peek('id', 'name', 'disabled', 'timeout')

    @property
    def course(self):
        if self.course_id:
            return Course.db().get(self.course_id)

    @property
    def description(self):
        if self.desc:
            return self.desc

        try:
            readme = os.path.join(Env.problems, self.course_id, self.id, 'README.md')
            with open(readme, 'r') as fp:
                import markdown
                return markdown.markdown(fp.read())
        except:
            pass

    @property
    def time_left(self):
        if not self.avail:
            return 10**10
        return int((self.avail - dt.datetime.now()).total_seconds())

    def is_active(self):
        return not self.disabled and self.time_left > 0

    @property
    def test_ids(self) -> typing.List[str]:
        return [test.id for test in self.tests]

    def tests_from_ids(self, ids: typing.List[str]):
        """
        :rtype: typing.List[ProblemCase]
        """
        result = []
        for id in ids:
            for test in self.tests:
                if test.id == id:
                    result.append(test)
                    break
        return result

    def get_reference(self):
        return self.reference


class ProblemCase(ADB):
    """
    :type id: str
    :type size: int
    :type random: int
    :type timeout: int
    :type problem: Problem
    """

    def __init__(self, item: dict, problem=None):
        super().__init__()
        self.id = item['id']
        self.size = item.get('size')
        self.timeout = item.get('timeout')
        self.problem = problem
        random = item.get('random')

        if random is True:
            self.random = 10
        elif random in (False, None):
            self.random = 0
        else:
            self.random = int(random)

    def generate_input_args(self, validate=False):
        if validate:
            return ['-v']

        args = list()
        if self.size:
            args += ['-p', self.size]

        if self.random:
            args += ['-r']

        return [str(x) for x in args]

    def cases(self):
        if not self.random:
            yield self
        else:
            for i in range(self.random):
                data = dict(
                    id='%s.%d' % (self.id, i),
                    size=self.size,
                    random=self.random,
                    timeout=self.timeout,
                )
                yield ProblemCase(data, self.problem)
