#!/bin/python3
# author: Jan Hybs
import os
import pathlib
import subprocess

import utils.io
from containers.docker import DockerAPI
from processing import docker_bash_template, ExecutorStatus
from processing.executors.local import LocalExecutor
from processing.result import ExecutorResult


class DockerExecutor(LocalExecutor):
    container = DockerAPI.create_container(
        image='automatest/all',
        name='automatest_cont',
        user='worker'
    )

    def __init__(self, global_limit, rand, filename, **kwargs):
        super().__init__(global_limit, **kwargs)
        self.cwd = kwargs['cwd']
        self.rand = rand
        self.dtmp = '/tmp/%s' % self.rand
        self.filename = filename

    def destroy(self):
        super().destroy()
        self.container.exec('rm -rf %s' % self.dtmp)

    def _cp(self, *files):
        for f in files:
            self.container.copy_to_container('%s/%s' % (self.cwd, f), '%s/%s' % (self.dtmp, f))

    def _run(self, cmd, soft_limit=0, *args, **kwargs):
        in_name = out_name = err_name = ''
        cwd_in = None
        tmp_dir = self.dtmp
        timeout = self._time_left
        pipeline_args = ' '.join(['"%s"' % x for x in cmd])
        timeout_args = 'timeout -t %1d -s 9' % int(timeout) if timeout else ''

        if self.stderr_path == subprocess.STDOUT:
            err_name = '2>&1'
        elif isinstance(self.stderr_path, pathlib.Path):
            err_name = '2>err'

        if isinstance(self.stdout_path, pathlib.Path):
            out_name = '>out'

        if isinstance(self.stdin_path, pathlib.Path):
            in_name = '<in'
            cwd_in = os.path.join(self.cwd, 'in')
            utils.io.write_file(cwd_in, self.stdin_path.read_text())

        # ----------
        bash_fmt = docker_bash_template.format(**locals())
        # print(bash_fmt)
        cwd_sh = os.path.join(self.cwd, '_main_.sh')
        utils.io.write_file(cwd_sh, bash_fmt)
        os.chmod(cwd_sh, 0o777)

        self.container.exec('mkdir -p %s' % tmp_dir)
        self._cp('_main_.sh', self.filename)
        if self.stdin_path:
            self._cp('in')

        cmd_output = self.container.exec('/bin/bash %s/_main_.sh' % tmp_dir).splitlines()
        # for i, l in enumerate(cmd_output):
        #     print('### %d)' % (i+1), l)
        # ----------

        try:
            returncode, start, stop = int(cmd_output[0]), float(cmd_output[1]), float(cmd_output[2])
        except ValueError:
            # skip first line because it says 'killed'
            returncode, start, stop = int(cmd_output[1]), float(cmd_output[2]), float(cmd_output[3])

        duration = max(1.0, stop - start)
        self._time_left -= duration

        if isinstance(self.stdout_path, pathlib.Path):
            utils.io.write_file(self.stdout_path, '')
            self.container.copy_from_container('%s/out' % tmp_dir, self.stdout_path)

        if isinstance(self.stderr_path, pathlib.Path):
            utils.io.write_file(self.stderr_path, '')
            self.container.copy_from_container('%s/err' % tmp_dir, self.stderr_path)

        if os.path.exists(cwd_sh):
            os.unlink(cwd_sh)

        if isinstance(self.stdin_path, pathlib.Path)  and os.path.exists(cwd_in):
            os.unlink(cwd_in)

        result = ExecutorResult(cmd)

        # killed or terminated
        if returncode in (137, 143):
            self.message = result.message = 'Terminated: global timeout was reached'
            return result(status=ExecutorStatus.GLOBAL_TIMEOUT, duration=duration)

            # determine result
        if returncode == 0:
            status = ExecutorStatus.OK
            self.message = result.message = 'ok'
            if soft_limit and duration > soft_limit:
                status = ExecutorStatus.SOFT_TIMEOUT
        else:
            status = ExecutorStatus.ERROR_WHILE_RUNNING

        return result(status=status, returncode=returncode, duration=duration)