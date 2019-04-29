#!/bin/python3
# author: Jan Hybs

import pathlib
import shutil
from uuid import uuid4

from loguru import logger

from env import Env
from processing import ExecutorStatus, ProcessRequestType
from processing.actions import AbstractAction
from processing.executors.multidocker import MultiDockerExecutor
from processing.executors.multilocal import MultiLocalExecutor
from processing.request import ProcessRequest, add_cmd_to_result, extract_console
from utils.timer import Timer


class ProcessRequestGenerateOutput(AbstractAction):
    type = ProcessRequestType.GENERATE_OUTPUT

    def __init__(self, request: ProcessRequest, result_dir: pathlib.Path, problem_dir: pathlib.Path):
        super().__init__(request, result_dir, problem_dir)

        self.uuid = uuid4().hex
        self.rand = '%s-%s' % (self.request.user.id, self.uuid)
        self._check_reference(self.request.problem.reference)

        if self.request.docker:
            self.executor = MultiDockerExecutor(Env.teacher_timeout, cwd=self.temp_dir)
        else:
            self.executor = MultiLocalExecutor(Env.teacher_timeout, cwd=self.temp_dir)

    def run(self):
        with Timer() as timer:
            solution_name = self.request.problem.reference.name
            self.temp_dir.joinpath(solution_name).write_text(
                self.problem_dir.joinpath(solution_name).read_text()
            )
            self.executor.prepare_files(self.request)
            self._compile()
            self._run()

        self.duration = timer.duration

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
                result = ex.run(cmd).register(id)

            # if ok we compare
            if result.status is ExecutorStatus.OK:
                result = add_cmd_to_result(result)

                # copy files
                shutil.copy(
                    subcase.temp.output,
                    subcase.problem.output,
                )

            # otherwise we try to extract errors
            else:
                result = extract_console(result)

            rr[id] = result
            request.event_execute_test.close_event.trigger(rr[id])
            logger.opt(ansi=True).info('{} - {}', log_base, rr[id])
