#!/bin/python3
# author: Jan Hybs

import pathlib
from uuid import uuid4

from loguru import logger

from env import Env
from processing import ExecutorStatus, ProcessRequestType
from processing.actions import AbstractAction
from processing.comparator import Comparator
from processing.executors.multidocker import MultiDockerExecutor
from processing.executors.multilocal import MultiLocalExecutor
from processing.request import ProcessRequest, Subcase, extract_console
from processing.result import ExecutorResult
from utils.timer import Timer


ONE_DAY = 60 * 60 * 24
HALF_DAY = 60 * 60 * 12


class ProcessRequestSolve(AbstractAction):
    type = ProcessRequestType.SOLVE

    def __init__(self, request: ProcessRequest, result_dir: pathlib.Path, problem_dir: pathlib.Path):
        super().__init__(request, result_dir, problem_dir)

        self.uuid = uuid4().hex
        self.rand = '%s-%s' % (self.request.user.id, self.uuid)
        self.solution_file = self.result_dir.joinpath('main.%s' % self.request.lang.extension)

        if self.request.docker:
            self.executor = MultiDockerExecutor(request.problem.timeout or Env.problem_timeout, cwd=self.temp_dir)
        else:
            self.executor = MultiLocalExecutor(request.problem.timeout or Env.problem_timeout, cwd=self.temp_dir)

    def run(self):
        with Timer() as timer:
            self.solution_file.write_text(self.request.solution)
            self.executor.prepare_files(self.request)
            self._compile()
            self._run()

        self.duration = timer.duration

    def compare_files(self, subcase: Subcase, result: ExecutorResult):
        compare_result = Comparator.compare_files(
            f1=subcase.problem.output,
            f2=subcase.temp.output
        )
        return self._evaluate_result(result, compare_result, subcase)

    def _run(self):
        request = self.request
        executor = self.executor
        cmd = self._run_cmd

        for subcase in request.iter_subcases():
            id = subcase.id

            if self._check_stdin_exists(subcase):
                logger.opt(ansi=True).info(
                    '{course.name}<b,g,>:</b,g,>{problem.id}<b,g,>:</b,g,>{case.id}',
                    case=subcase, problem=request.problem, course=request.course
                )
            else:
                request[id].status = ExecutorStatus.SKIPPED
                request[id].message = 'skipped'
                request[id].console = 'Input file does not exists'.splitlines()
                request.event_execute_test.close_event.trigger(
                    request, request[id]
                )
                continue

            # actually execute the code

            request[id].status = ExecutorStatus.RUNNING
            request.event_execute_test.open_event.trigger(
                request, request[id]
            )
            with executor.set_streams(**subcase.temp_files(self.type)) as ex:
                timeout = (subcase.timeout or Env.case_timeout) * request.lang.scale
                result = ex.run(cmd, soft_limit=timeout).register(id)

            # if ok we compare
            if result.status in (ExecutorStatus.OK, ExecutorStatus.SOFT_TIMEOUT):
                result = self.compare_files(subcase, result)

            # otherwise we try to extract errors
            else:
                result = extract_console(result)

            request[id] = result
            request._register_attachment(id=id, name='input', path=subcase.temp.input)
            request._register_attachment(id=id, name='output', path=subcase.temp.output)
            request._register_attachment(id=id, name='error', path=subcase.temp.error)
            request._register_attachment(id=id, name='reference', path=subcase.problem.output)

            request.event_execute_test.close_event.trigger(
                request, request[id]
            )
