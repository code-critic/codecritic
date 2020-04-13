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


class ProcessRequestGenerateInput(AbstractAction):
    type = ProcessRequestType.GENERATE_INPUT

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
        cmd_base = self._run_cmd
        logger.opt(ansi=True).info('<red>{}</red> - {}', 'RUNNING', cmd_base)

        
        for index, subcase in enumerate(request.iter_subcases()):
            id = subcase.id

            if not subcase.case.size:
                logger.opt(ansi=True).warning(
                    '{course.name}<b><e>:</e></b>{problem.id}<b><e>:</e></b>{case.id} - '
                    'Cannot generate input file, property '
                    '"<b><e>size</e></b>" not specified',
                    case=subcase.case, problem=request.problem, course=request.course
                )
                rr[id].status = ExecutorStatus.IGNORE
                rr[id].message = 'Test skipped'
                rr[id].console = 'Cannot generate input file, property "size" not specified'
                request.event_execute_test.open_event.trigger(rr[id])
                continue

            log_base = self.case_log_format.format(case=subcase.subcase, problem=request.problem, course=request.course)
            cmd = cmd_base + subcase.subcase.generate_input_args(index=index + 1)

            logger.opt(ansi=True).debug('{} - {}', log_base, cmd)
            rr[id].status = ExecutorStatus.RUNNING
            request.event_execute_test.open_event.trigger(rr[id])
            with executor.set_streams(**subcase.temp_files(self.type)) as ex:
                result = ex.run(cmd).register(id)

            if result.status is ExecutorStatus.OK:
                result = add_cmd_to_result(result)

                # copy files
                shutil.copy(
                    subcase.temp.input,
                    subcase.problem.input,
                )
            else:
                result = extract_console(result)

            rr[id] = result
            request.event_execute_test.open_event.trigger(rr[id])
            logger.opt(ansi=True).info('{} - {}', log_base, rr[id])
