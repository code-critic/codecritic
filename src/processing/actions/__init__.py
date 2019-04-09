#!/bin/python3
# author: Jan Hybs
import pathlib
import subprocess
import typing

from loguru import logger

from database.objects import Script
from processing.comparator import Comparator
from processing.executors.local import LocalExecutor
from processing.result import ExecutorResult
from processing import ExecutorStatus
from processing.request import ProcessRequest, FatalException, add_cmd_to_result


class AbstractAction(object):
    def __init__(self, request: ProcessRequest, result_dir: pathlib.Path):
        self.request = request
        self.result_dir = pathlib.Path(result_dir)
        self.executor = None
        self.duration = 0.0

    def destroy(self):
        if self.executor:
            self.executor.destroy()

    def run(self):
        pass

    @classmethod
    def _compile_raw(cls, request: ProcessRequest, pipeline: list, executor: LocalExecutor, out_dir: typing.Union[str, pathlib.Path]):
        if not pipeline:
            return

        result_id = 'compilation'
        request._compile_result = ExecutorResult.empty_result(result_id, ExecutorStatus.RUNNING)
        request.event_compile.open_event.trigger(request, request._compile_result)

        inn = None
        out = pathlib.Path(out_dir).joinpath('.compile.log')
        err = subprocess.STDOUT
        cmd = pipeline

        logger.opt(ansi=True).info('<red>{}</red>: {}', 'COMPILING', cmd)
        with executor.set_streams(stdin=inn, stdout=out, stderr=err) as ex:
            result = ex.run(cmd)

        if result.failed():
            if result.status is ExecutorStatus.GLOBAL_TIMEOUT:
                raise FatalException('Compilation was interrupted (did not finish in time)', details=result.stdout)
            else:
                raise FatalException('Compilation failed', details=result.stdout)

        request._compile_result = add_cmd_to_result(result_id, result).register(result_id)
        request.event_compile.close_event.trigger(request, request._compile_result)

        return result

    @classmethod
    def _solve_raw(cls, request, pipeline: list, executor: LocalExecutor, in_dir, out_dir, err_dir, ref_out):
        cmd = pipeline
        logger.opt(ansi=True).info('<red>{}</red> - {}', 'RUNNING', cmd)

        for id, case, subcase in request:
            inn = pathlib.Path(in_dir).joinpath(subcase.id)
            out = pathlib.Path(out_dir).joinpath(subcase.id)
            err = pathlib.Path(err_dir).joinpath(subcase.id)
            ref = pathlib.Path(ref_out).joinpath(subcase.id)

            if inn.exists():
                logger.opt(ansi=True).info(
                    '{course.name}<b,g,>:</b,g,>{problem.id}<b,g,>:</b,g,>{case.id}',
                    case=subcase, problem=request.problem, course=request.course
                )
            else:
                logger.opt(ansi=True).warning(
                    '{course.name}<b,g,>:</b,g,>{problem.id}<b,g,>:</b,g,>{case.id} - '
                    'input file does not exists, test will be skipped',
                    case=subcase, problem=request.problem, course=request.course
                )
                request[id].status = ExecutorStatus.SKIPPED
                request[id].message = 'skipped'
                request[id].console = 'Input file does not exists'.splitlines()
                request.event_execute_test.close_event.trigger(
                    request, request[id]
                )
                continue

            request[id].status = ExecutorStatus.RUNNING
            request.event_execute_test.open_event.trigger(
                request, request[id]
            )

            with executor.set_streams(stdin=inn, stdout=out, stderr=err) as ex:
                result = ex.run(cmd).register(id)

            # if ok we compare
            if result.status in (ExecutorStatus.OK, ExecutorStatus.SOFT_TIMEOUT):
                compare_result = Comparator.compare_files(
                    f1=ref,
                    f2=out
                )
                result = cls._evaluate_result(result, compare_result, subcase)
                result.add_attachment(
                    dict(path=inn, name='input'),
                    dict(path=out, name='output'),
                    dict(path=err, name='error'),
                    dict(path=ref, name='reference'),
                )

            request[id] = result
            request[id] = add_cmd_to_result(id, request[id])
            request.event_execute_test.close_event.trigger(
                request, request[id]
            )

    @classmethod
    def _check_reference(cls, reference: Script):
        if not reference or not reference.lang_ref:
            raise FatalException('Reference not specified', [
                'No reference was specified in course yaml file.',
                'Do not know how to generate input.',
                'Please add reference field to the course yaml file:'
                '',
                '  reference:',
                '    name: main.py',
                '    lang: PY-367',
            ])
        return True

    @classmethod
    def _evaluate_result(cls, result, compare_result, subcase):
        if compare_result:
            # CORRECT RESULT
            if result.status is ExecutorStatus.OK:
                result.message = 'Submitted solution is correct'
                result.status = ExecutorStatus.ANSWER_CORRECT

            # CORRECT RESULT BUT TIMED OUT
            elif result.status is ExecutorStatus.SOFT_TIMEOUT:
                result.message = 'Submitted solution is correct but does not meet runtime criteria'
                result.message_details = 'Allowed time is %1.3sec but was running for %1.3f sec' % (
                    subcase.timeout, result.duration
                )
                result.status = ExecutorStatus.ANSWER_CORRECT_TIMEOUT
        else:
            # INCORRECT RESULT
            if result.status is ExecutorStatus.OK:
                result.message = 'Submitted solution is incorrect'
                result.status = ExecutorStatus.ANSWER_WRONG

            # INCORRECT RESULT AND TIMED OUT
            elif result.status is ExecutorStatus.SOFT_TIMEOUT:
                result.message = 'Submitted solution is incorrect and does not meet runtime criteria'
                result.message_details = 'Allowed time is %1.3sec but was running for %1.3f sec' % (
                    subcase.timeout, result.duration
                )
                result.status = ExecutorStatus.ANSWER_WRONG_TIMEOUT

            result.console = compare_result.message
        return result
