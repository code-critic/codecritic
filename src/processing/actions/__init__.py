#!/bin/python3
# author: Jan Hybs
import pathlib
import subprocess
import typing

from loguru import logger

from env import Env
from database.objects import Script
from processing.comparator import Comparator
from processing.result import ExecutorResult
from processing import ExecutorStatus, ProcessRequestType
from processing.request import ProcessRequest, add_cmd_to_result, _configure_cmd, Subcase
from exceptions import FatalException, CompileException


class AbstractAction(object):
    """
    :type executor: processing.executors.multilocal.MultiLocalExecutor or processing.executors.multidocker.MultiLocalExecutor
    """
    def __init__(self, request: ProcessRequest, result_dir: pathlib.Path, problem_dir: pathlib.Path):
        self.request = request
        self.result_dir = pathlib.Path(result_dir)
        self.temp_dir = pathlib.Path(result_dir)
        self.problem_dir = pathlib.Path(problem_dir)
        self.executor = None
        self.duration = 0.0

    def destroy(self):
        if self.executor:
            self.executor.destroy()

    def run(self):
        pass

    def _compile(self):
        cmd = self._compile_cmd
        if not cmd:
            return

        result_id = 'compilation'
        self.request._compile_result = ExecutorResult.empty_result(result_id, ExecutorStatus.RUNNING)
        self.request.event_compile.open_event.trigger(self.request, self.request._compile_result)

        out = self.temp_dir / '.compile.log'
        logger.opt(ansi=True).info('<red>{}</red>: {}', 'COMPILING', cmd)
        with self.executor.set_streams(stdin=None, stdout=out, stderr=out) as ex:
            result = ex.run(cmd, Env.compile_timeout)

        self.request._compile_result = add_cmd_to_result(result_id, result).register(result_id)

        if result.failed():
            if result.status is ExecutorStatus.GLOBAL_TIMEOUT:
                raise CompileException('Compilation was interrupted (did not finish in time)', details=result.read_stdout())
            else:
                result.status = ExecutorStatus.COMPILATION_FAILED
                raise CompileException('Compilation failed', details=result.read_stdout())

        self.request.event_compile.close_event.trigger(self.request, self.request._compile_result)

        return result

    def _check_stdin_exists(self, subcase: Subcase):
        if not subcase.temp_stdin.exists():
            logger.opt(ansi=True).warning(
                '{course.name}<b,g,>:</b,g,>{problem.id}<b,g,>:</b,g,>{case.id} - '
                'input file does not exists, test will be skipped',
                case=subcase.subcase, problem=self.request.problem, course=self.request.course
            )
            return False
        return True

    @property
    def _compile_cmd(self):
        if self.request.type is ProcessRequestType.SOLVE:
            pipeline = self.request.lang.compile
            name = 'main.%s' % self.request.lang.extension

        elif self.request.type in (ProcessRequestType.GENERATE_INPUT, ProcessRequestType.GENERATE_OUTPUT):
            if self.request.problem.reference:
                pipeline = self.request.problem.reference.lang_ref.compile
                name = self.request.problem.reference.name
            else:
                pipeline, name = None, None
        else:
            logger.error('Invalid action type')
            raise FatalException('Invalid action type {}', self.request.type)

        if not pipeline:
            return None

        return _configure_cmd(
            pipeline,
            name
        )

    @property
    def _run_cmd(self):
        if self.request.type is ProcessRequestType.SOLVE:
            pipeline = self.request.lang.run
            name = 'main.%s' % self.request.lang.extension

        elif self.request.type in (ProcessRequestType.GENERATE_INPUT, ProcessRequestType.GENERATE_OUTPUT):
            if self.request.problem.reference:
                pipeline = self.request.problem.reference.lang_ref.run
                name = self.request.problem.reference.name
            else:
                pipeline, name = None, None
        else:
            logger.error('Invalid action type')
            raise FatalException('Invalid action type {}', self.request.type)

        if not pipeline:
            return None

        return _configure_cmd(
            pipeline,
            name
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
