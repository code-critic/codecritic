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
            if self.solution_file.exists() and Env.debug_mode:
                logger.debug('not saving cource code in debug mode')
            else:
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
        rr = self.request.result
        executor = self.executor
        cmd = self._run_cmd

        for subcase in request.iter_subcases():
            id = subcase.id

            if not self._check_stdin_exists(subcase):
                rr[id].status = ExecutorStatus.SKIPPED
                rr[id].message = 'skipped'
                rr[id].console = 'Input file does not exists'.splitlines()
                request.event_execute_test.close_event.trigger(rr[id])
                continue

            log_base = self.case_log_format.format(case=subcase.subcase, problem=request.problem, course=request.course)
            logger.opt(ansi=True).debug('{} - {}', log_base, cmd)

            # actually execute the code

            rr[id].status = ExecutorStatus.RUNNING
            request.event_execute_test.open_event.trigger(rr[id])
            with executor.set_streams(**subcase.temp_files(self.type)) as ex:
                timeout = (subcase.timeout or Env.case_timeout) * request.lang.scale
                result = ex.run(cmd, soft_limit=timeout).register(id)

            # if ok we compare
            if result.status in (ExecutorStatus.OK, ExecutorStatus.SOFT_TIMEOUT):
                result = self.compare_files(subcase, result)

            # otherwise we try to extract errors
            else:
                result = extract_console(result)

            rr[id] = result
            rr[id].attachments.extend(subcase.subcase.get_attachments(subcase.temp_dir))

            request.event_execute_test.close_event.trigger(rr[id])
