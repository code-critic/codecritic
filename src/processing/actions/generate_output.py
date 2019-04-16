#!/bin/python3
# author: Jan Hybs

import pathlib
import shutil
from uuid import uuid4

from loguru import logger

from env import Env
from processing import ExecutorStatus
from processing.actions import AbstractAction
from processing.executors.multilocal import MultiLocalExecutor
from processing.executors.multidocker import MultiDockerExecutor
from processing.request import ProcessRequest, _configure_cmd, add_cmd_to_result, extract_console
from utils.timer import Timer


class ProcessRequestGenerateOutput(AbstractAction):
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

            with executor.set_streams(stdin=subcase.temp_stdin, stdout=subcase.temp_stdout, stderr=subcase.temp_stderr) as ex:
                result = ex.run(cmd).register(id)

            # if ok we compare
            if result.status is ExecutorStatus.OK:
                result = add_cmd_to_result(id, result)

                # copy files
                shutil.copy(
                    subcase.temp_stdout,
                    subcase.problem_stdout
                )

            # otherwise we try to extract errors
            else:
                result = extract_console(result)

            request[id] = result

            request.event_execute_test.close_event.trigger(
                request, request[id]
            )
