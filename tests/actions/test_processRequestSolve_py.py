#!/bin/python3
# author: Jan Hybs

import pathlib
import unittest

import pytest

from database.objects import User
from processing import ExecutorStatus, ProcessRequestType
from processing.request import ProcessRequest


case = unittest.TestCase('__init__')
root = pathlib.Path(__file__).resolve()
files = root.parent / 'files'

user_root = User(dict(
    id='root',
    role='test',
))

solution_py_correct = files / 'problem-1-correct.py'
solution_py_wrong = files / 'problem-1-wrong.py'
solution_py_timeout = files / 'problem-1-timeout.py'
solution_py_fatal = files / 'problem-1-fatal.py'

request_base = dict(
    user=user_root,
    lang='PY-367',
    type=ProcessRequestType.SOLVE,
    course='TST-2019',
    problem='problem-1',
)

request_base_cpp = dict(
    user=user_root,
    lang='CPP',
    type=ProcessRequestType.SOLVE,
    course='TGH-2019',
    problem='WEBISL',
)

use_docker_args = [
    pytest.param(True, marks=pytest.mark.docker),
    pytest.param(False, marks=pytest.mark.no_docker),
]


# -----------------------------------------------------------------------------


@pytest.mark.parametrize('use_docker', use_docker_args)
def test_correct(use_docker):
    request = ProcessRequest(
        solution=solution_py_correct.read_text(),
        docker=use_docker,
        **request_base
    )
    request.process()

    evaluation = request._evaluation
    case.assertIs(evaluation.status, ExecutorStatus.ANSWER_CORRECT)

    for subcase in request.iter_subcases():
        result = request[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ANSWER_CORRECT)


@pytest.mark.parametrize('use_docker', use_docker_args)
def test_wrong(use_docker):
    request = ProcessRequest(
        solution=solution_py_wrong.read_text(),
        docker=use_docker,
        **request_base
    )
    request.process()

    evaluation = request._evaluation
    case.assertIs(evaluation.status, ExecutorStatus.ANSWER_WRONG)

    for subcase in request.iter_subcases():
        result = request[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ANSWER_WRONG)


@pytest.mark.parametrize('use_docker', use_docker_args)
def test_timeout(use_docker):
    request = ProcessRequest(
        solution=solution_py_timeout.read_text(),
        docker=use_docker,
        **request_base
    )
    request.process()

    evaluation = request._evaluation
    case.assertIs(evaluation.status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)

    case.assertIs(request['case-1.s'].status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
    case.assertGreater(request['case-1.s'].duration, 1.0)
    case.assertIs(request['case-2'].status, ExecutorStatus.ANSWER_CORRECT)
    case.assertIs(request['case-3.0'].status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
    case.assertIs(request['case-3.1'].status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
    case.assertIs(request['case-3.2'].status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
    case.assertIs(request['case-3.3'].status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
    case.assertIs(request['case-3.4'].status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)


@pytest.mark.parametrize('use_docker', use_docker_args)
def test_fatal(use_docker):
    request = ProcessRequest(
        solution=solution_py_fatal.read_text(),
        docker=use_docker,
        **request_base
    )
    request.process()

    evaluation = request._evaluation
    case.assertIs(evaluation.status, ExecutorStatus.ERROR_WHILE_RUNNING)

    for subcase in request.iter_subcases():
        result = request[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ERROR_WHILE_RUNNING)
        case.assertIn('!!!FOOBAR!!!', result.stderr.read_text())
