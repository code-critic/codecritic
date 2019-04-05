#!/bin/python3
# author: Jan Hybs

import pathlib
from uuid import uuid4

from loguru import logger

from env import Env
from processing.actions import AbstractAction
from processing.executors.docker import DockerExecutor
from processing.executors.local import LocalExecutor
from processing import ExecutorStatus
from processing.request import ProcessRequest, _configure_cmd, add_cmd_to_result
from utils.timer import Timer


class ProcessRequestGenerateInput(AbstractAction):
    def __init__(self, request: ProcessRequest, result_dir: pathlib.Path):
        super().__init__(request, result_dir)

        self.uuid = uuid4().hex
        self.rand = '%s-%s' % (self.request.user.id, self.uuid)
        self.problem_dir = pathlib.Path(Env.problems, self.request.course.id, self.request.problem.id)
        self._check_reference(self.request.problem.reference)

        if self.request.docker:
            self.executor = DockerExecutor(Env.teacher_timeout, cwd=self.problem_dir,
                                           rand=self.rand, filename=self.request.problem.reference.name)
        else:
            self.executor = LocalExecutor(Env.teacher_timeout, cwd=self.problem_dir)

    def run(self):
        with Timer() as timer:
            self._compile()
            self._run()

        self.duration = timer.duration

    def _compile(self):
        return self._compile_raw(
            self.request,
            _configure_cmd(
                self.request.problem.reference.lang_ref.compile,
                self.request.problem.reference.name
            ),
            self.executor,
            self.problem_dir
        )

    def _run(self):
        cmd_base = _configure_cmd(
            self.request.problem.reference.lang_ref.run or ['main'],
            self.request.problem.reference.name
        )
        logger.opt(ansi=True).info('<red>{}</red> - {}', 'RUNNING', cmd_base)

        for id, case, subcase in self.request:
            if not case.size:
                logger.opt(ansi=True).warning(
                    '{course.name}<b,e,>:</b,e,>{problem.id}<b,e,>:</b,e,>{case.id} - '
                    'Cannot generate input file, property '
                    '"<b,e,>size</b,e,>" not specified',
                    case=case, problem=self.request.problem, course=self.request.course
                )
                self.request[id].status = ExecutorStatus.IGNORE
                self.request[id].message = 'Test skipped'
                self.request[id].console = 'Cannot generate input file, property "size" not specified'
                self.request.event_execute_test.close_event.trigger(
                    self.request, self.request[id]
                )
                continue

            inn = None
            out = self.problem_dir.joinpath('input', subcase.id)
            err = self.problem_dir.joinpath('.error', subcase.id)
            cmd = cmd_base + subcase.generate_input_args()

            logger.opt(ansi=True).info(
                '{course.name}<b,g,>:</b,g,>{problem.id}<b,g,>:</b,g,>{case.id} - {}',
                cmd, case=subcase, problem=self.request.problem, course=self.request.course
            )
            self.request[id].status = ExecutorStatus.RUNNING
            self.request.event_execute_test.open_event.trigger(
                self.request, self.request[id]
            )
            with self.executor.set_streams(stdin=inn, stdout=out, stderr=err) as ex:
                result = ex.run(cmd).register(id)

            self.request[id] = result
            self.request[id] = add_cmd_to_result(id, self.request[id])
            self.request.event_execute_test.close_event.trigger(
                self.request, self.request[id]
            )
