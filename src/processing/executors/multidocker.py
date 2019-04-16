#!/bin/python3
# author: Jan Hybs

import pathlib
import time
import uuid

from loguru import logger

from containers.docker import DockerAPI
from processing import ProcessRequestType, ExecutorStatus
from processing.executors.multilocal import MultiLocalExecutor
from processing.request import ProcessRequest
from processing.result import ExecutorResult


docker_bash_template = '''
#!/bin/bash
cd {self.docker_temp_dir}
START=$(python3 -c "import time; print(time.time())")
timeout -t ${{1:-60}} -s 9 {pipeline_args} {in_name} {out_name} {err_name}
echo $?
END=$(python3 -c "import time; print(time.time())")
echo $START
echo $END
'''


class MultiDockerExecutor(MultiLocalExecutor):
    container = DockerAPI.create_container(
        image='automatest/all',
        name='automatest_cont',
        user='worker'
    )

    def __init__(self, global_limit: float, cwd: pathlib.Path, **kwargs):
        super().__init__(global_limit, cwd, **kwargs)

        self.cwd = cwd
        self.kwargs = kwargs
        self.rand = 'd-%s' % uuid.uuid4()
        self.docker_temp_dir = pathlib.Path('/tmp').joinpath(self.rand)

    def prepare_files(self, request: ProcessRequest):
        # copy local files
        super().prepare_files(request)

        # copy all files to docker
        self.container.exec('mkdir -p %s' % self.docker_temp_dir)
        self.container.copy_to_container('%s/.' % self.cwd, self.docker_temp_dir)
        self.container.exec('chown -R worker %s' % self.docker_temp_dir, user='root')

    def copy_out_files(self):
        try:
            self.container.copy_from_container('%s/.' % self.docker_temp_dir, self.cwd)
        except Exception as e:
            logger.exception('Could not copy files from docker {}', self.docker_temp_dir)

    def _run(self, cmd, soft_limit, *args, **kwargs):
        result = ExecutorResult(cmd)

        self.stdin_fp, self.stdout_fp, self.stderr_fp = None, None, None
        if self.stdin_path:
            self.stdin_fp = self.stdin_path.relative_to(self.cwd)

        if self.stdout_path:
            self.stdout_fp = self.stdout_path.relative_to(self.cwd)

        if self.stderr_path:
            self.stderr_fp = self.stderr_path.relative_to(self.cwd)

        docker_cmd = [
            'python3', '/bin/run.py',
            '---t', str(int(self._time_left)),
            '---w', str(self.docker_temp_dir),
        ]

        if self.stdin_fp:
            docker_cmd += ['---i', self.stdin_fp]

        if self.stdout_fp:
            docker_cmd += ['---o', self.stdout_fp]

        if self.stderr_fp:
            docker_cmd += ['---e', self.stderr_fp]

        docker_cmd.extend(cmd)
        cmd_str = ' '.join([str(x) for x in docker_cmd])

        st = time.time()
        cmd_output = self.container.exec(cmd_str).splitlines()
        duration = time.time() - st

        logger.info('Executing docker run.py {}', cmd_str)

        try:
            returncode, duration = int(cmd_output[0]), float(cmd_output[1])
        except Exception as e:
            # fatal error inside docker
            returncode, duration = 666, duration

        self.decrease_timepool(duration)
        result.duration = duration
        result.returncode = returncode

        if returncode == 667:
            result.message = 'File not found'
            result.status = ExecutorStatus.FILE_NOT_FOUND

        elif returncode == 666:
            result.message = 'Terminated: global timeout was reached'
            result.status = ExecutorStatus.GLOBAL_TIMEOUT

        elif returncode == 0:
            if soft_limit and duration > soft_limit:
                result.status = ExecutorStatus.SOFT_TIMEOUT
            else:
                result.status = ExecutorStatus.OK
        else:
            result.status = ExecutorStatus.ERROR_WHILE_RUNNING

        self.copy_out_files()
        result.stdin = self.stdin_path
        result.stdout = self.stdout_path
        result.stderr = self.stderr_path
        return result

    def destroy(self):
        super().destroy()
        try:
            self.container.exec('rm -rf %s' % self.docker_temp_dir, user='root')
        except:
            logger.exception('Could not delete tmp folder {}', self.docker_temp_dir)
