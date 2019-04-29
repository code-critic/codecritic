#!/bin/python3
# author: Jan Hybs
from exceptions import CompileException
from processing import ExecutorStatus
from processing.request import ProcessRequest
from .conftest import pytest, pytest_matrix, conf_setup_function, conf_teardown_function, case, solve_request_base

setup_function = conf_setup_function
teardown_function = conf_teardown_function


# -----------------------------------------------------------------------------

@pytest.mark.parametrize('use_docker', pytest_matrix)
def test_solution_correct(use_docker, solution_correct):
    request = ProcessRequest(
        src=solution_correct.read_text(),
        docker=use_docker,
        **solve_request_base
    )
    request.process()

    evaluation = request.result.result
    case.assertIs(evaluation.status, ExecutorStatus.ANSWER_CORRECT)
    case.assertIs(request.result.compilation.status, ExecutorStatus.OK)

    for subcase in request.iter_subcases():
        result = request.result[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ANSWER_CORRECT)


@pytest.mark.parametrize('use_docker', pytest_matrix)
def test_solution_wrong(use_docker, solution_wrong):
    request = ProcessRequest(
        src=solution_wrong.read_text(),
        docker=use_docker,
        **solve_request_base
    )
    request.process()

    evaluation = request.result.result
    case.assertIs(evaluation.status, ExecutorStatus.ANSWER_WRONG)
    case.assertIs(request.result.compilation.status, ExecutorStatus.OK)

    for subcase in request.iter_subcases():
        result = request.result[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ANSWER_WRONG)


@pytest.mark.parametrize('use_docker', pytest_matrix)
def test_solution_timeout(use_docker, solution_timeout):
    request = ProcessRequest(
        src=solution_timeout.read_text(),
        docker=use_docker,
        **solve_request_base
    )
    request.process()

    evaluation = request.result.result
    case.assertIs(evaluation.status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
    case.assertIs(request.result.compilation.status, ExecutorStatus.OK)

    for subcase in request.iter_subcases():
        result = request.result[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)


@pytest.mark.parametrize('use_docker', pytest_matrix)
def test_solution_fatal(use_docker, solution_fatal):
    request = ProcessRequest(
        src=solution_fatal.read_text(),
        docker=use_docker,
        **solve_request_base
    )
    request.process()

    evaluation = request.result.result
    case.assertIs(evaluation.status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request.result.compilation.status, ExecutorStatus.OK)

    for subcase in request.iter_subcases():
        result = request.result[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ERROR_WHILE_RUNNING)


@pytest.mark.parametrize('use_docker', pytest_matrix)
def test_solution_fatal_compile(use_docker, solution_fatal_compile):
    request = ProcessRequest(
        src=solution_fatal_compile.read_text(),
        docker=use_docker,
        **solve_request_base
    )

    with case.assertRaises(CompileException):
        request.process()

    evaluation = request.result.result
    case.assertIs(evaluation.status, ExecutorStatus.COMPILATION_FAILED)
    case.assertIs(request.result.compilation.status, ExecutorStatus.COMPILATION_FAILED)

    for subcase in request.iter_subcases():
        result = request.result[subcase.id]
        case.assertIs(result.status, ExecutorStatus.SKIPPED)
