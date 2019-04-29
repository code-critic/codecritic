# #!/bin/python3
# # author: Jan Hybs

from processing import ExecutorStatus
from processing.request import ProcessRequest
from .conftest import pytest, pytest_matrix, conf_setup_function, conf_teardown_function, case, generate_output_request_base

setup_function = conf_setup_function
teardown_function = conf_teardown_function


# -----------------------------------------------------------------------------


@pytest.mark.parametrize('use_docker', pytest_matrix)
def test_solution_correct(use_docker, solution_correct):
    request = ProcessRequest(
        src=None,
        docker=use_docker,
        **generate_output_request_base
    )
    request.process()

    evaluation = request.result.result
    case.assertIs(evaluation.status, ExecutorStatus.OK)

    case.assertIs(request.result['case-1.s'].status, ExecutorStatus.OK)
    case.assertIs(request.result['case-2'].status, ExecutorStatus.OK)
    case.assertIs(request.result['case-3.0'].status, ExecutorStatus.OK)
    case.assertIs(request.result['case-3.1'].status, ExecutorStatus.OK)
    case.assertIs(request.result['case-3.2'].status, ExecutorStatus.OK)
    case.assertIs(request.result['case-3.3'].status, ExecutorStatus.OK)
    case.assertIs(request.result['case-3.4'].status, ExecutorStatus.OK)


@pytest.mark.parametrize('use_docker', pytest_matrix)
def test_solution_fatal(use_docker, solution_fatal):
    request = ProcessRequest(
        src=None,
        docker=use_docker,
        **generate_output_request_base
    )
    request.process()

    evaluation = request.result.result
    case.assertIs(evaluation.status, ExecutorStatus.ERROR_WHILE_RUNNING)

    case.assertIs(request.result['case-1.s'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request.result['case-2'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request.result['case-3.0'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request.result['case-3.1'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request.result['case-3.2'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request.result['case-3.3'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIs(request.result['case-3.4'].status, ExecutorStatus.ERROR_WHILE_RUNNING)
    case.assertIn('!!!FOOBAR!!!', request.result['case-3.4'].stderr.read_text())
