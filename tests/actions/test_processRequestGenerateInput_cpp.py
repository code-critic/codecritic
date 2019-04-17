#!/bin/python3
# author: Jan Hybs

import pathlib
import unittest

import pytest

from database.objects import User, Courses
from env import Env
from processing import ExecutorStatus, ProcessRequestType
from processing.request import ProcessRequest


case = unittest.TestCase('__init__')
root = pathlib.Path(__file__).resolve()
files = root.parent / 'files'

user_root = User(dict(
    id='root',
    role='test',
))

tgh_config = files / 'TGH.config.yaml'
solution_cpp_correct = files / 'problem-2-correct.cpp'
solution_cpp_wrong = files / 'problem-2-wrong.cpp'
solution_cpp_timeout = files / 'problem-2-timeout.cpp'
solution_cpp_fatal = files / 'problem-2-fatal.cpp'
solution_cpp_fatal_compile = files / 'problem-1-correct.py'


request_base = dict(
    user=user_root,
    lang='CPP',
    type=ProcessRequestType.GENERATE_INPUT,
    course='TGH-2019',
    problem='WEBISL',
)

use_docker_args = [
    pytest.param(True, marks=pytest.mark.docker),
    pytest.param(False, marks=pytest.mark.no_docker),
]


def write_files(f: pathlib.Path):
    (Env.courses / 'TGH' / '2019' / 'config.yaml').write_text(
        tgh_config.read_text()
    )

    course = Courses()[request_base['course']]
    problem = course.problem_db[request_base['problem']]

    problem.reference.path.write_text(f.read_text())

# -----------------------------------------------------------------------------


@pytest.mark.parametrize('use_docker', use_docker_args)
def test_ok(use_docker):
    write_files(solution_cpp_correct)
    request = ProcessRequest(
        solution=None,
        docker=use_docker,
        **request_base
    )
    request.process()

    evaluation = request._evaluation
    case.assertIs(evaluation.status, ExecutorStatus.OK)
    case.assertIs(request._compile_result.status, ExecutorStatus.OK)

    for subcase in request.iter_subcases():
        result = request[subcase.id]
        case.assertIs(result.status, ExecutorStatus.OK)


@pytest.mark.parametrize('use_docker', use_docker_args)
def test_fatal(use_docker):
    write_files(solution_cpp_fatal)
    request = ProcessRequest(
        solution=None,
        docker=use_docker,
        **request_base
    )
    request.process()

    evaluation = request._evaluation
    case.assertIs(evaluation.status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request._compile_result.status, ExecutorStatus.OK)

    for subcase in request.iter_subcases():
        result = request[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ERROR_WHILE_RUNNING)
