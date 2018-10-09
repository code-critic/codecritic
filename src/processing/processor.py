#!/bin/python3
# author: Jan Hybs
import os
import subprocess as sp
from signal import SIGKILL
import time

from cfg.problems import StaticTest
from cfg.requests import Request
from containers.docker import DockerAPI
from processing.statuses import RequestResult, ResultStatus
from utils.events import MultiEvent
from utils.io import write_file, read_file
from utils.strings import random_string
from utils.timer import Timer


class RunCrate(object):
    def __init__(self, returncode=None, stdin=None, stdout=None, stderr=None, duration=None):
        self.duration = duration
        self.stderr = stderr
        self.stdout = stdout
        self.stdin = stdin
        self.returncode = returncode  # type: int

    def __repr__(self):
        return 'Crate<\n    {self.returncode}\n    stderr:\n{self.stderr}\n    stdout:\n{self.stdout}>'.format(self=self)

    @staticmethod
    def ensure_iterable(o):
        if o is None:
            return []
        if isinstance(o, str):
            return o.splitlines()
        if isinstance(o, list):
            return o
        return list(o)

    def reverse_streams(self):
        tmp = self.stderr
        self.stderr = self.stdout
        self.stdout = tmp
        return self

    def peek(self):
        return dict(
            duration=self.duration,
            returncode=self.returncode,
            stderr=self.ensure_iterable(self.stderr),
            stdout=self.ensure_iterable(self.stdout),
        )


class DockerExecutor(object):
    container = DockerAPI.get_container('ada19')
    bash_template = '''
#!/bin/bash,
cd {tmp_dir}
START=$(date +%s.%N)
{timeout_args} {pipeline_args} < in > out 2> err
echo $?
END=$(date +%s.%N)
echo $START
echo $END
'''.strip()

    def __init__(self):
        self.dtmp = '/tmp/tmp.%d.%s' % (time.time(), random_string(8))

    def _run(self, pipeline, input_file, output_file, error_file, cwd, timeout=None):
        tmp_dir = self.dtmp
        pipeline_args = ' '.join(['"%s"' % x for x in pipeline])
        timeout_args = 'timeout %f' % timeout if timeout else ''
        bash_fmt = self.bash_template.format(**locals())

        cwd_in = os.path.join(cwd, 'in')
        cwd_sh = os.path.join(cwd, '_main_.sh')

        write_file(cwd_in, read_file(input_file))
        write_file(cwd_sh, bash_fmt)
        os.chmod(cwd_sh, 0o777)

        self.container.exec('mkdir -p %s' % tmp_dir)
        self.container.copy_to_container('%s/.' % cwd, tmp_dir)

        with Timer('exec %s' % pipeline, None) as timer:
            cmd_output = self.container.exec('/bin/bash %s/_main_.sh' % tmp_dir).splitlines()
            returncode, start, stop = int(cmd_output[0]), float(cmd_output[1]), float(cmd_output[2])
            duration = stop - start

        write_file(output_file, '')
        self.container.copy_from_container('%s/out' % tmp_dir, output_file)
        write_file(error_file, '')
        self.container.copy_from_container('%s/err' % tmp_dir, error_file)
        os.unlink(cwd_sh)

        output, error = read_file(output_file), read_file(error_file)

        if returncode == 124:   # timeout
            return RunCrate(returncode=None, stderr='Time limit exceeded!', duration=duration)

        print(RunCrate(returncode=returncode, stdout=output, stderr=error, duration=duration).peek())
        return RunCrate(returncode=returncode, stdout=output, stderr=error, duration=duration)

    def run(self, pipeline, input_file, output_file, error_file, cwd, timeout=None):
        return self._run(pipeline, input_file, output_file, error_file, cwd, timeout)

    def clean_up(self):
        self.container.exec('rm -rf %s' % self.dtmp)


class LocalExecutor(object):

    def clean_up(self):
        pass

    @classmethod
    def _run(cls, pipeline, input_file, output_file, error_file, cwd, timeout=None):
        process = sp.Popen(pipeline, stderr=sp.PIPE, stdout=sp.PIPE, stdin=sp.PIPE, cwd=cwd)
        input = read_file(input_file, 'rb')
        try:
            output, error = process.communicate(input, timeout=timeout)
        except sp.TimeoutExpired as e:
            os.kill(process.pid, SIGKILL)
            print('Killing', process.pid)
            return RunCrate(stderr='Time limit exceeded!')

        output, error = output.decode(), error.decode()

        write_file(output_file, output)
        write_file(error_file, error)

        return RunCrate(returncode=process.returncode, stdout=output, stderr=error)

    @classmethod
    def run(cls, pipeline, input_file, output_file, error_file, cwd, timeout=None):
        return cls._run(pipeline, input_file, output_file, error_file, cwd, timeout)


class Processor(object):

    def __init__(self, request: Request):
        self.event_process = MultiEvent('on-process')

        self.event_compile = MultiEvent('on-compile')
        self.event_execute = MultiEvent('on-execute')

        self.event_compare_test = MultiEvent('on-compare-test')
        self.event_execute_test = MultiEvent('on-execute-test')

        self.request = request

        if request.use_docker:
            self.executor = DockerExecutor()
        else:
            self.executor = LocalExecutor()

    def start(self):
        with self.event_process.target(self.request):
            self.request.running = True
            result = self._start()
            self.executor.clean_up()
            return result

    def _start(self):
        request = self.request
        result = RequestResult(request)

        if request.action is Request.Action.TEST:

            if request.lang.compile:
                result.compilation.result, crate = self.compile_solution(request)
                result.compilation.error = crate.stderr

                # check compilation result
                if result.compilation.result != ResultStatus.COMPILE_OK:
                    return result

            test_result = dict(tests=request.tests)
            with self.event_execute.target(request, test_result):
                for test in request.tests:
                    test_solution = result.tests[test.id]
                    test_solution.result, crate = self.execute_solution(request, test)
                    test_solution.error = crate.stderr

                    if test_solution.result not in (ResultStatus.ANSWER_OK, ResultStatus.EXECUTE_OK):
                        # exit right away when using docker (or on demand)
                        if request.abort_on_error:
                            return result
                test_result['status'] = ResultStatus.EXECUTE_OK.name

            return result

        elif request.action is Request.Action.GENERATE_OUTPUT:

            if request.lang.compile:
                result.compilation.result, crate = self.compile_solution(request)
                result.compilation.error = crate.stderr

                # check compilation result
                if result.compilation.result != ResultStatus.COMPILE_OK:
                    return result

            for test in request.tests:
                test_solution = result.tests[test.id]
                test_solution.result, crate = self.generate_output(request, test)
                test_solution.error = crate.stderr

                if test_solution.result not in (ResultStatus.ANSWER_OK, ResultStatus.EXECUTE_OK):
                    if request.abort_on_error:
                        return result

            return result

    def compile_solution(self, request):

        result = dict()
        # fire compile start and end events
        with self.event_compile.target(request, result):
            pipeline = [x.format(**request.config) for x in request.lang.compile]

            output_dir = os.path.join(request.root, 'compile')
            output_file = os.path.join(output_dir, 'compile')
            error_file = os.path.join(output_dir, 'error')
            os.makedirs(output_dir, 0o777, True)

            crate = self.executor.run(pipeline, None, output_file, error_file, request.root, 30.0)

            if crate.returncode is None:
                result['status'] = ResultStatus.GLOBAL_TIMEOUT.name
                result['info'] = crate
                return ResultStatus.GLOBAL_TIMEOUT, crate

            if crate.returncode != 0:
                result['status'] = ResultStatus.COMPILE_ERROR.name
                result['info'] = crate
                return ResultStatus.COMPILE_ERROR, crate

            result['status'] = ResultStatus.COMPILE_OK.name
            result['info'] = crate
            return ResultStatus.COMPILE_OK, crate

    def execute_solution(self, request: Request, test: StaticTest):

        result = dict()
        # fire execute start and end events
        with self.event_execute_test.target(request, test, result):
            pipeline = [x.format(**request.config) for x in request.lang.execute]

            output_dir = os.path.join(request.root, 'output')
            output_file = os.path.join(output_dir, test.id)
            error_file = os.path.join(output_dir, 'error')
            os.makedirs(output_dir, 0o777, True)

            crate = self.executor.run(pipeline, test.input, output_file, error_file, request.root, test.time)

            if crate.returncode is None:
                result['status'] = ResultStatus.GLOBAL_TIMEOUT.name
                result['info'] = crate
                return ResultStatus.GLOBAL_TIMEOUT, crate

            if crate.returncode != 0:
                result['status'] = ResultStatus.EXECUTE_ERROR.name
                result['info'] = crate
                return ResultStatus.EXECUTE_ERROR, crate

            if request.compare:
                compare_result, crate = self.compare_files(test.output, output_file)
                result['status'] = compare_result.name
                result['info'] = crate
                return compare_result, crate

            result['status'] = ResultStatus.ANSWER_OK.name
            result['info'] = crate

        return ResultStatus.ANSWER_OK, crate

    # --------------------------------------------------------------------------------------------

    @classmethod
    def write_result(cls, request: Request, result: RequestResult, location=None):
        # print(result.result)
        location = location if location else request.root
        write_file(
            os.path.join(location, 'result.yaml'),
            result.to_yaml()
        )
        write_file(
            os.path.join(location, request.file),
            request.source_code
        )
        # print(result.to_yaml())

    @staticmethod
    def compare_files(f1, f2, keep_going=True):
        error = list()
        output = list()
        result = True

        lines1 = read_file(f1).splitlines()
        lines2 = read_file(f2).splitlines()

        lenl1 = len(lines1)
        lenl2 = len(lines2)

        for i in range(max(lenl1, lenl2)):
            l1 = lines1[i] if i < lenl1 else '""'
            l2 = lines2[i] if i < lenl2 else '""'
            output.append(l2)

            if l1 != l2:
                error.extend([
                    'chyba na radku %d: ' % (i+1),
                    '        ocekavan:   "%s"' % l1,
                    '         nalezen:   "%s"' % l2,
                    ''
                ])
                result = False
                if not keep_going:
                    break

        if result:
            return ResultStatus.ANSWER_OK, RunCrate(stderr=output)
        else:
            return ResultStatus.ANSWER_WRONG, RunCrate(stderr=error)

    def generate_output(self, request: Request, test: StaticTest):
        pipeline = [x.format(**request.config) for x in request.lang.execute]

        crate = self.executor.run(pipeline, test.input, test.output, test.error, request.root, 15.0)

        if crate.returncode is None:
            return ResultStatus.GLOBAL_TIMEOUT, crate

        if crate.returncode != 0:
            return ResultStatus.EXECUTE_ERROR, crate

        return ResultStatus.EXECUTE_OK, crate.reverse_streams()
