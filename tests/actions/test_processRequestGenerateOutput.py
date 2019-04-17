# #!/bin/python3
# # author: Jan Hybs

import pathlib
import unittest

import pytest

from database.objects import Courses, User
from processing import ExecutorStatus, ProcessRequestType
from processing.request import ProcessRequest


case = unittest.TestCase('__init__')
root = pathlib.Path(__file__).resolve()

user_root = User(dict(
    id='root',
    role='test',
))

solution_py_correct = (root.parent / 'files' / 'problem-1-correct.py')
solution_py_wrong = (root.parent / 'files' / 'problem-1-wrong.py')
solution_py_timeout = (root.parent / 'files' / 'problem-1-timeout.py')
solution_py_fatal = (root.parent / 'files' / 'problem-1-fatal.py')

request_base = dict(
    user=user_root,
    lang='PY-367',
    type=ProcessRequestType.GENERATE_OUTPUT,
    course='TST-2019',
    problem='problem-1',
    cases=None,
)

use_docker_args = [
    pytest.param(True, marks=pytest.mark.docker),
    pytest.param(False, marks=pytest.mark.no_docker),
]


# -----------------------------------------------------------------------------


@pytest.mark.parametrize('use_docker', use_docker_args)
def test_ok(use_docker):
    course = Courses()[request_base['course']]
    problem = course.problem_db[request_base['problem']]
    problem.reference.path.write_text(
        solution_py_correct.read_text()
    )

    request = ProcessRequest(
        solution=None,
        docker=use_docker,
        **request_base
    )
    request.process()

    evaluation = request._evaluation
    case.assertIs(evaluation.status, ExecutorStatus.OK)

    case.assertIs(request['case-1.s'].status, ExecutorStatus.OK)
    case.assertIs(request['case-2'].status, ExecutorStatus.OK)
    case.assertIs(request['case-3.0'].status, ExecutorStatus.OK)
    case.assertIs(request['case-3.1'].status, ExecutorStatus.OK)
    case.assertIs(request['case-3.2'].status, ExecutorStatus.OK)
    case.assertIs(request['case-3.3'].status, ExecutorStatus.OK)
    case.assertIs(request['case-3.4'].status, ExecutorStatus.OK)


@pytest.mark.parametrize('use_docker', use_docker_args)
def test_fatal(use_docker):
    course = Courses()[request_base['course']]
    problem = course.problem_db[request_base['problem']]
    problem.reference.path.write_text(
        solution_py_fatal.read_text()
    )

    request = ProcessRequest(
        solution=None,
        docker=use_docker,
        **request_base
    )
    request.process()

    evaluation = request._evaluation
    case.assertIs(evaluation.status, ExecutorStatus.ERROR_WHILE_RUNNING)

    case.assertIs(request['case-1.s'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request['case-2'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request['case-3.0'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request['case-3.1'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request['case-3.2'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request['case-3.3'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request['case-3.4'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIn('!!!FOOBAR!!!', request['case-3.4'].stderr.read_text())
