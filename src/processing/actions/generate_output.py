#!/bin/python3
# author: Jan Hybs

import pathlib
from uuid import uuid4

from env import Env
from processing.actions import AbstractAction
from processing.executors.docker import DockerExecutor
from processing.executors.local import LocalExecutor
from processing.request import ProcessRequest, _configure_cmd
from utils.timer import Timer


class ProcessRequestGenerateOutput(AbstractAction):
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
        self._solve_raw(
            self.request,
            _configure_cmd(
                self.request.problem.reference.lang_ref.run or ['main'],
                self.request.problem.reference.name
            ),
            self.executor,
            self.problem_dir.joinpath('input'),
            self.problem_dir.joinpath('output'),
            self.problem_dir.joinpath('.error'),
            self.problem_dir.joinpath('output'),
            teacher=True
        )
