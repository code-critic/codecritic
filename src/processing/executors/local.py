#!/bin/python3
# author: Jan Hybs
import shutil
import subprocess
import subprocess as sp

from loguru import logger

from processing import ExecutorStatus
from processing.result import ExecutorResult
from utils import timer


class LocalExecutor(object):
    """
    :type stdin: utils.io.FileEx
    :type stdout: utils.io.FileEx
    :type stderr: utils.io.FileEx
    """
    stream_map = [
        ('stdin', 'stdin_fp', 'stdin_path', 'r'),
        ('stdout', 'stdout_fp', 'stdout_path', 'w'),
        ('stderr', 'stderr_fp', 'stderr_path', 'w'),
    ]

    def __init__(self, global_limit, **kwargs):
        self.kwargs = kwargs
        self.global_limit = global_limit
        self._time_left = self.global_limit

        self.stdout = self.stdin = self.stderr = None
        self.stdout_path = self.stdin_path = self.stderr_path = None
        self.stdout_fp = self.stdin_fp = self.stderr_fp = None
        self.message = None
        self.delete_dir =None

    def set_streams(self, **kwargs):
        for stream, stream_fp, stream_path, m in self.stream_map:
            if stream in kwargs:
                setattr(self, stream_path, kwargs[stream])
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def _open_streams(self):
        for stream, stream_fp, stream_path, m in self.stream_map:
            if hasattr(getattr(self, stream_path), 'open'):
                try:
                    getattr(self, stream_path).parent.mkdir(parents=True, exist_ok=True)
                    fp = getattr(self, stream_path).open(m)
                    setattr(self, stream_fp, fp)
                except: pass
            elif getattr(self, stream_path) == subprocess.STDOUT:
                setattr(self, stream_fp, subprocess.STDOUT)

        return self

    def _close_streams(self, result=None):
        for stream, stream_fp, stream_path, m in self.stream_map:
            setattr(self, stream, list())

            if hasattr(getattr(self, stream_fp), 'close'):
                getattr(self, stream_fp).close()
                setattr(self, stream_fp, None)

            if hasattr(getattr(self, stream_path), 'read_text'):
                try:
                    content = getattr(self, stream_path).read_text().splitlines()
                    setattr(self, stream, content)
                    if result:
                        setattr(result, stream, content)
                except:
                    pass

    def run(self, cmd, soft_limit=0, *args, **kwargs):
        if self._time_left <= 0:
            self.message = 'Test was skipped (no time left)'
            result = ExecutorResult(cmd, status=ExecutorStatus.SKIPPED)
            result.message = self.message
            return result

        self.message = None
        self._open_streams()
        result = self._run(cmd, soft_limit, *args, **kwargs)
        self._close_streams(result)
        result.message = self.message
        return result

    def _run(self, cmd, soft_limit=0, *args, **kwargs):
        cp = self.kwargs.copy()
        cp.update(dict(
            stdin=self.stdin_fp,
            stdout=self.stdout_fp,
            stderr=self.stderr_fp,
        ))
        cp.update(kwargs)
        result = ExecutorResult(cmd)

        with timer.Timer() as t:
            # try to execute the command
            try:
                print(cmd, args, cp)
                process = sp.Popen(cmd, *args, **cp)
            except FileNotFoundError as ex:
                duration = t.duration
                self._time_left -= duration
                self.message = 'File not found'
                return result(status=ExecutorStatus.FILE_NOT_FOUND, error=ex, duration=duration)

            # try to wait for the command to finish
            try:
                rc = process.wait(self._time_left)
            except sp.TimeoutExpired as ex:
                duration = t.duration
                self._time_left -= duration
                process.kill()
                self.message = 'Terminated: global timeout was reached'
                return result(status=ExecutorStatus.GLOBAL_TIMEOUT, error=ex, duration=duration)

        # decrease limit
        duration = t.duration
        self._time_left -= duration

        # determine result
        if rc == 0:
            status = ExecutorStatus.OK
            if soft_limit and t.duration > soft_limit:
                status = ExecutorStatus.SOFT_TIMEOUT
        else:
            status = ExecutorStatus.ERROR_WHILE_RUNNING

        return result(status=status, returncode=rc, duration=duration)

    def destroy(self):
        if self.delete_dir:
            logger.info('deleting {}', self.delete_dir)
            shutil.rmtree(self.delete_dir, ignore_errors=True)
