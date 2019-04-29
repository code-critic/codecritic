#!/bin/python3
# author: Jan Hybs

from processing import ExecutorStatus
from processing.request import ProcessRequest
from .conftest import pytest, pytest_matrix, conf_setup_function, conf_teardown_function, case, solve_request_base

setup_function = conf_setup_function
teardown_function = conf_teardown_function


# -----------------------------------------------------------------------------


@pytest.mark.parametrize('use_docker', pytest_matrix)
def test_correct(use_docker, solution_correct):
    request = ProcessRequest(
        src=solution_correct.read_text(),
        docker=use_docker,
        **solve_request_base
    )
    request.process()

    evaluation = request.result.result
    case.assertIs(evaluation.status, ExecutorStatus.ANSWER_CORRECT)

    for subcase in request.iter_subcases():
        result = request.result[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ANSWER_CORRECT)


@pytest.mark.parametrize('use_docker', pytest_matrix)
def test_wrong(use_docker, solution_wrong):
    request = ProcessRequest(
        src=solution_wrong.read_text(),
        docker=use_docker,
        **solve_request_base
    )
    request.process()

    evaluation = request.result.result
    case.assertIs(evaluation.status, ExecutorStatus.ANSWER_WRONG)

    for subcase in request.iter_subcases():
        result = request.result[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ANSWER_WRONG)


@pytest.mark.parametrize('use_docker', pytest_matrix)
def test_timeout(use_docker, solution_timeout):
    request = ProcessRequest(
        src=solution_timeout.read_text(),
        docker=use_docker,
        **solve_request_base
    )
    request.process()

    evaluation = request.result.result
    case.assertIs(evaluation.status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)

    case.assertIs(request.result['case-1.s'].status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
    case.assertGreater(request.result['case-1.s'].duration, 1.0)

    case.assertIs(request.result['case-2'].status, ExecutorStatus.ANSWER_CORRECT)
    case.assertIs(request.result['case-3.0'].status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
    case.assertIs(request.result['case-3.1'].status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
    case.assertIs(request.result['case-3.2'].status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
    case.assertIs(request.result['case-3.3'].status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
    case.assertIs(request.result['case-3.4'].status, ExecutorStatus.ANSWER_CORRECT_TIMEOUT)


@pytest.mark.parametrize('use_docker', pytest_matrix)
def test_fatal(use_docker, solution_fatal):
    request = ProcessRequest(
        src=solution_fatal.read_text(),
        docker=use_docker,
        **solve_request_base
    )
    request.process()

    evaluation = request.result.result
    case.assertIs(evaluation.status, ExecutorStatus.ERROR_WHILE_RUNNING)

    for subcase in request.iter_subcases():
        result = request.result[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ERROR_WHILE_RUNNING)
        case.assertIn('!!!FOOBAR!!!', result.stderr.read_text())
