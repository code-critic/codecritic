# #!/bin/python3
# # author: Jan Hybs

from processing import ExecutorStatus
from processing.request import ProcessRequest
from .conftest import pytest, pytest_matrix, conf_setup_function, conf_teardown_function, case, generate_output_request_base

setup_function = conf_setup_function
teardown_function = conf_teardown_function


# -----------------------------------------------------------------------------


@pytest.mark.parametrize('use_docker', pytest_matrix)
def test_ok(use_docker, solution_correct):
    request = ProcessRequest(
        src=None,
        docker=use_docker,
        **generate_output_request_base
    )
    request.process()

    evaluation = request.result.result
    case.assertIs(evaluation.status, ExecutorStatus.OK)
    case.assertIs(request.result.compilation.status, ExecutorStatus.OK)

    for subcase in request.iter_subcases():
        result = request.result[subcase.id]
        case.assertIs(result.status, ExecutorStatus.OK)


@pytest.mark.parametrize('use_docker', pytest_matrix)
def test_fatal(use_docker, solution_fatal):
    request = ProcessRequest(
        src=None,
        docker=use_docker,
        **generate_output_request_base
    )
    request.process()

    evaluation = request.result.result
    case.assertIs(evaluation.status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request.result.compilation.status, ExecutorStatus.OK)

    for subcase in request.iter_subcases():
        result = request.result[subcase.id]
        case.assertIs(result.status, ExecutorStatus.ERROR_WHILE_RUNNING)
