#!/bin/python3
# author: Jan Hybs

import pathlib
import unittest

import pytest

from database.objects import User
from env import Env
from exceptions import CompileException
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
    type=ProcessRequestType.SOLVE,
    course='TGH-2019',
    problem='WEBISL',
)

use_docker_args = [
    pytest.param(True, marks=pytest.mark.docker),
    pytest.param(False, marks=pytest.mark.no_docker),
]


def write_tgh_cfg():
    (Env.courses / 'TGH' / '2019' / 'config.yaml').write_text(
        tgh_config.read_text()
    )


# -----------------------------------------------------------------------------


@pytest.mark.parametrize('use_docker', use_docker_args)
def test_correct_cpp(use_docker):
    write_tgh_cfg()

    request = ProcessRequest(
        solution=solution_cpp_correct.read_text(),
        docker=use_docker,
        **request_base
    )
    request.process()

    evaluation = request._evaluation
    case.assertIs(evaluation.status, ExecutorStatus.ANSWER_CORRECT)
    case.assertIs(request._compile_result.status, ExecutorStatus.OK)

    for subcase in request.iter_subcases():
        result = request[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ANSWER_CORRECT)


@pytest.mark.parametrize('use_docker', use_docker_args)
def test_wrong_cpp(use_docker):
    write_tgh_cfg()

    request = ProcessRequest(
        solution=solution_cpp_wrong.read_text(),
        docker=use_docker,
        **request_base
    )
    request.process()

    evaluation = request._evaluation
    case.assertIs(evaluation.status, ExecutorStatus.ANSWER_WRONG)
    case.assertIs(request._compile_result.status, ExecutorStatus.OK)

    for subcase in request.iter_subcases():
        result = request[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ANSWER_WRONG)


@pytest.mark.parametrize('use_docker', use_docker_args)
def test_timeout_cpp(use_docker):
    write_tgh_cfg()

    request = ProcessRequest(
        solution=solution_cpp_timeout.read_text(),
        docker=use_docker,
        **request_base
    )
    request.process()

    evaluation = request._evaluation
    case.assertIs(evaluation.status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
    case.assertIs(request._compile_result.status, ExecutorStatus.OK)

    for subcase in request.iter_subcases():
        result = request[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)


@pytest.mark.parametrize('use_docker', use_docker_args)
def test_fatal_cpp(use_docker):
    write_tgh_cfg()

    request = ProcessRequest(
        solution=solution_cpp_fatal.read_text(),
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


@pytest.mark.parametrize('use_docker', use_docker_args)
def test_fatal_compile_cpp(use_docker):
    write_tgh_cfg()

    request = ProcessRequest(
        solution=solution_cpp_fatal_compile.read_text(),
        docker=use_docker,
        **request_base
    )

    with case.assertRaises(CompileException):
        request.process()

    evaluation = request._evaluation
    case.assertIs(evaluation.status, ExecutorStatus.COMPILATION_FAILED)
    case.assertIs(request._compile_result.status, ExecutorStatus.COMPILATION_FAILED)

    for subcase in request.iter_subcases():
        result = request[subcase.id]
        case.assertIs(result.status, ExecutorStatus.SKIPPED)
