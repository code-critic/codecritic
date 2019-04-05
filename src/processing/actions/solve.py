#!/bin/python3
# author: Jan Hybs
import os
import pathlib
import time
from uuid import uuid4

from env import Env
from processing.actions import AbstractAction
from processing.executors.docker import DockerExecutor
from processing.executors.local import LocalExecutor
from processing.request import ProcessRequest, _configure_cmd
from utils.timer import Timer

ONE_DAY = 60*60*24
HALF_DAY = 60*60*12


class ProcessRequestSolve(AbstractAction):
    def __init__(self, request: ProcessRequest, result_dir: pathlib.Path):
        super().__init__(request, result_dir)

        self.uuid = uuid4().hex
        self.rand = '%s-%s' % (self.request.user.id, self.uuid)
        self.problem_dir = pathlib.Path(Env.problems, self.request.course.id, self.request.problem.id)
        self.solution_file = self.result_dir.joinpath('main.%s' % self.request.lang.extension)

        self.delete_old_dirs(self.result_dir.parent)

        if self.request.docker:
            self.executor = DockerExecutor(request.problem.timeout or Env.problem_timeout, cwd=self.result_dir,
                                           rand=self.rand, filename='main.%s' % self.request.lang.extension)
            self.executor.delete_dir = self.result_dir
        else:
            self.executor = LocalExecutor(request.problem.timeout or Env.problem_timeout, cwd=self.result_dir)
            self.executor.delete_dir = self.result_dir

    def delete_old_dirs(self, tmp_dir: pathlib.Path, seconds=HALF_DAY):
        ts = int(time.time())

        for d in tmp_dir.glob('*'):
            print(d)
            if d.is_dir():
                modif = int(os.path.getmtime(d))
                if (ts - modif) > seconds:
                    print('will delete dir ', d)
                print(ts - modif, modif, ts)
            print()

    def run(self):
        with Timer() as timer:
            self.solution_file.parent.mkdir(parents=True, exist_ok=True)
            self.solution_file.write_text(self.request.solution)

            self._compile()
            self._run()

        self.duration = timer.duration

    def _compile(self):
        return self._compile_raw(
            self.request,
            _configure_cmd(
                self.request.lang.compile,
                'main.%s' % self.request.lang.extension
            ),
            self.executor,
            self.result_dir
        )

    def _run(self):
        self._solve_raw(
            self.request,
            _configure_cmd(
                self.request.lang.run,
                'main.%s' % self.request.lang.extension
            ),
            self.executor,
            self.problem_dir.joinpath('input'),
            self.result_dir.joinpath('output'),
            self.result_dir.joinpath('.error'),
            self.problem_dir.joinpath('output'),
        )
