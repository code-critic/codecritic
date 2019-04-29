#!/bin/python3
# author: Jan Hybs

import inspect
import pathlib
import unittest
import sys

import pytest
from loguru import logger
from database.objects import Courses, User
from env import Env
from processing import ProcessRequestType

logger.configure(
    handlers=[dict(sink=sys.stdout, colorize=False, level='INFO')]
)


case = unittest.TestCase('__init__')
language = pytest.mark.cpp
pytest_matrix = [
    pytest.param(True, marks=[pytest.mark.docker, language]),
    pytest.param(False, marks=[pytest.mark.no_docker, language]),
]

root = pathlib.Path(__file__).resolve()
files = root.parent.parent / 'files'

_course_name = 'TGH'
_course_config = files / 'TGH.config.yaml'
_solution = dict(
    solution_correct=files / 'problem-2-correct.cpp',
    solution_wrong=files / 'problem-2-wrong.cpp',
    solution_timeout=files / 'problem-2-timeout.cpp',
    solution_fatal=files / 'problem-2-fatal.cpp',
    solution_fatal_compile=files / 'problem-1-correct.py',
)

user_root = User(dict(
    id='root',
    role='test',
))

request_base = dict(
    user=user_root,
    lang='CPP',
    course='TGH-2019',
    problem='WEBISL',
)

solve_request_base = dict(
    type=ProcessRequestType.SOLVE,
    **request_base
)
generate_input_request_base = dict(
    type=ProcessRequestType.GENERATE_INPUT,
    **request_base
)
generate_output_request_base = dict(
    type=ProcessRequestType.GENERATE_OUTPUT,
    **request_base
)


def write_config(reference: pathlib = None):
    (Env.courses / _course_name / '2019' / 'config.yaml').write_text(
        _course_config.read_text()
    )

    if reference:
        course = Courses()[request_base['course']]
        problem = course.problem_db[request_base['problem']]
        problem.reference.path.write_text(
            reference.read_text()
        )


def conf_setup_function(function):
    # func_name = function.__code__.co_name
    # for k, v in _solution.items():
    #     if k in func_name:
    #         return write_config(v)
    args = inspect.getfullargspec(function).args
    for k, v in _solution.items():
        if k in args:
            return write_config(v)
    return write_config()


def conf_teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    pass


@pytest.fixture()
def solution_correct():
    return _solution['solution_correct']


@pytest.fixture()
def solution_wrong():
    return _solution['solution_wrong']


@pytest.fixture()
def solution_fatal():
    return _solution['solution_fatal']


@pytest.fixture()
def solution_fatal_compile():
    return _solution['solution_fatal_compile']


@pytest.fixture()
def solution_timeout():
    return _solution['solution_timeout']
