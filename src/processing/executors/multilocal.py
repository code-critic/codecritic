#!/bin/python3
# author: Jan Hybs

import pathlib
import shutil
import subprocess

from loguru import logger

from processing import ProcessRequestType, ExecutorStatus
from processing.request import ProcessRequest, OptionalPath
from processing.result import ExecutorResult
from utils import timer


class MultiLocalExecutor(object):
    """
    :type stdin_path: pathlib.Path
    :type stdout_path: pathlib.Path
    :type stderr_path: pathlib.Path

    :type stdin_fp: io.TextIOWrapper
    :type stdout_fp: io.TextIOWrapper
    :type stderr_fp: io.TextIOWrapper
    """
    def __init__(self, global_limit: float, cwd: pathlib.Path, **kwargs):
        """

        :param global_limit: global limit of this Executor
        :param cwd: path to the tmp working directory, where everything will be stored
        :param kwargs: additional arguments passed to the Popen
        """
        self.global_limit = global_limit
        self._time_left = self.global_limit
        self.cwd = cwd
        self.kwargs = kwargs
        self.kwargs['cwd'] = cwd

        self.stdin_fp, self.stdout_fp,self.stderr_fp = None, None, None
        self.stdin_path,self.stdout_path, self.stderr_path = None, None, None

    def prepare_files(self, request: ProcessRequest):
        """
        This method will copy files to a tmp dir
        (based on a request type)
        :param request:
        :return:
        """
        for subcase in request.iter_subcases():
            if subcase.needs_input:
                if subcase.problem_stdin.exists():
                    shutil.copyfile(subcase.problem_stdin, subcase.temp_stdin)

    def set_streams(self, stdin: OptionalPath =None, stdout: OptionalPath=None, stderr: OptionalPath=None):
        self.stdin_fp, self.stdout_fp, self.stderr_fp = None, None, None
        self.stdin_path, self.stdout_path, self.stderr_path = stdin, stdout, stderr
        return self

    def _open_streams(self):
        if self.stdin_path:
            self.stdin_fp = self.stdin_path.open('r')

        if self.stdout_path:
            self.stdout_fp = self.stdout_path.open('w')

        if self.stderr_path:
            if self.stdout_path == self.stderr_path:
                self.stderr_fp = subprocess.STDOUT
            else:
                self.stderr_fp = self.stderr_path.open('w')

    def _close_streams(self):
        for fp in self.stdin_fp, self.stdout_fp, self.stderr_fp:
            try:
                fp.close()
            except: pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def decrease_timepool(self, value: float):
        logger.info('decreasing time pool by {} ({} left)', value, self._time_left)
        self._time_left -= value
        return self

    def run(self, cmd, soft_limit=0, *args, **kwargs):
        if self._time_left <= 0:
            result = ExecutorResult(cmd, status=ExecutorStatus.SKIPPED)
            result.message = 'Test was skipped (no time left)'
            return result

        return self._run(cmd, soft_limit, *args, **kwargs)

    def _run(self, cmd, soft_limit, *args, **kwargs):
        result = ExecutorResult(cmd)

        self._open_streams()
        kw = self.kwargs.copy()
        kw['stdin'] = self.stdin_fp
        kw['stdout'] = self.stdout_fp
        kw['stderr'] = self.stderr_fp
        kw.update(**kwargs)

        with timer.Timer() as t:
            # try to execute the command
            try:
                logger.info('running cmd {}, {}, {}', cmd, args, kw)
                process = subprocess.Popen(cmd, *args, **kw)
            except FileNotFoundError as ex:
                duration = t.duration
                self.decrease_timepool(duration)
                result.message = 'File not found'
                self._close_streams()
                return result(status=ExecutorStatus.FILE_NOT_FOUND, error=ex, duration=duration)

            # try to wait for the command to finish
            try:
                rc = process.wait(self._time_left)
            except subprocess.TimeoutExpired as ex:
                duration = t.duration
                self.decrease_timepool(duration)
                process.kill()
                result.message = 'Terminated: global timeout was reached'
                self._close_streams()
                return result(status=ExecutorStatus.GLOBAL_TIMEOUT, error=ex, duration=duration)

        # decrease limit
        duration = t.duration
        self.decrease_timepool(duration)
        result.stdin = self.stdin_path
        result.stdout = self.stdout_path
        result.stderr = self.stderr_path

        # determine result
        if rc == 0:
            status = ExecutorStatus.OK
            if soft_limit and t.duration > soft_limit:
                status = ExecutorStatus.SOFT_TIMEOUT
        else:
            status = ExecutorStatus.ERROR_WHILE_RUNNING

        return result(status=status, returncode=rc, duration=duration)

    def destroy(self):
        pass
