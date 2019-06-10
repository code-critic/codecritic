#!/bin/python3
# author: Jan Hybs

import os
import os
import pathlib
import shutil
import typing

from entities.crates import TestResult
from utils.paths import IOEPaths


OptionalPath = typing.Optional[pathlib.Path]

from exceptions import FatalException, CompileException, ConfigurationException
from uuid import uuid4

from loguru import logger

from database.objects import Course, Courses, Languages, Problem, User, ProblemCase
from env import Env
from processing import ExecutorStatus, ProcessRequestType
from processing.result import ExecutorResult, RequestResult
from utils.events import MultiEvent


def hook_warn_empty_input(id, result: ExecutorResult):
    if not result.stdin:
        raise FatalException('Input file is empty', ['please double check your input files for test', id])
    return result


def add_cmd_to_result(result: ExecutorResult):
    if not result.console:
        result.console = ' '.join(result.cmd)
    return result


def extract_console(result: ExecutorResult):
    if result.failed():
        stderr = result.read_stderr()
        if stderr:
            result.console = stderr
        else:
            stdout = result.read_stdout()
            result.console = stdout

    return result


class Subcase(object):
    def __init__(self, id: str, case: ProblemCase, subcase: ProblemCase, temp_dir: pathlib.Path, problem_dir: pathlib.Path, needs_input=True):
        self.id = id
        self.case = case
        self.subcase = subcase
        self.temp_dir = temp_dir
        self.problem_dir = problem_dir
        self.timeout = self.subcase.timeout
        self.needs_input = needs_input

        self.temp = IOEPaths(temp_dir).ioe_files(id)
        self.problem = IOEPaths(problem_dir).ioe_files(id)

    def temp_files(self, type: ProcessRequestType=ProcessRequestType.SOLVE):
        if type in (ProcessRequestType.SOLVE, ProcessRequestType.GENERATE_OUTPUT):
            return dict(
                stdin=self.temp.input,
                stdout=self.temp.output,
                stderr=self.temp.output,
            )
        if type is ProcessRequestType.GENERATE_INPUT:
            return dict(
                stdin=None,
                stdout=self.temp.input,
                stderr=self.temp.output,
            )


class ProcessRequest(object):
    """
    :type course: Course
    :type problem: Problem
    :type lang: Languages
    :type user: User
    :type action_executor: processing.actions.AbstractAction
    """

    def __init__(self, user: User, lang, type, src, course, problem, cases=None, docker=True, **kwargs):
        self.course = Courses()[course]
        self.problem = self.course.problem_db[problem]
        self.lang = Languages.db().get(lang)
        self.case_ids = cases or self.problem.test_ids
        self.cases = self.problem.tests_from_ids(self.case_ids)

        self.user = user
        self.solution = src
        self.type = ProcessRequestType(type)
        self.docker = docker

        self.uuid = uuid4().hex
        self.rand = '%s-%s' % (self.user.id, self.uuid)

        if Env.debug_mode:
            logger.debug('using pseudo random tmp dir in debug mode')
            self.rand = 'jan.hybs-DEBUG'

        self.action_executor = None
        self.subcases = None
        self.result = RequestResult(self)

        self.event_process = MultiEvent('on-process')
        self.event_compile = MultiEvent('on-compile')
        self.event_execute_test = MultiEvent('on-execute-test')

        self.problem_dir = pathlib.Path(self.course.problems_dir, self.problem.id)
        self.result_dir = pathlib.Path(Env.tmp, self.rand)
        self.temp_dir = pathlib.Path(Env.tmp, self.rand)

        self.problem_dirs = IOEPaths(self.problem_dir).mkdir()
        self.temp_dirs = IOEPaths(self.temp_dir).mkdir()
        self.is_running = False

    def __repr__(self):
        return ('Request(\n'
                '  user={self.user.id}\n'
                '  course={self.course.name}\n'
                '  problem={self.problem.id}\n'
                '  language={self.lang}\n'
                '  type={self.type}\n'
                ')').format(self=self)

    def peek(self, full: bool=True):
        return TestResult(
            uuid=self.uuid,
            user=self.user.id,
            course=self.course.id,
            lang=self.lang.id if self.lang else None,
            problem=self.problem.id,
            action=str(self.type.value),
            result=self.result.peek(full) if self.result else None,
            docker=self.docker,
        )

    # ------------------------------------------

    def process(self):
        self.is_running = True
        self.result.result.message = 'Processing'
        self.result.result.status = ExecutorStatus.RUNNING

        # no tests provided
        if not self.result.subcases:
            self.event_process.open_event.trigger(self.result)
            self.evaluate_solution()
            self.event_process.close_event.trigger(self.result)
            raise ConfigurationException('No tests provided in yaml config file')

        # emit event
        if self.type is ProcessRequestType.GENERATE_INPUT:
            from processing.actions.generate_input import ProcessRequestGenerateInput
            self.action_executor = ProcessRequestGenerateInput(self, self.result_dir, self.problem_dir)

        elif self.type is ProcessRequestType.GENERATE_OUTPUT:
            from processing.actions.generate_output import ProcessRequestGenerateOutput
            self.action_executor = ProcessRequestGenerateOutput(self, self.result_dir, self.problem_dir)

        elif self.type is ProcessRequestType.SOLVE:
            from processing.actions.solve import ProcessRequestSolve
            self.action_executor = ProcessRequestSolve(self, self.result_dir, self.problem_dir)
        else:
            raise FatalException('Unsupported action {}'.format(self.type))

        self.event_process.open_event.trigger(self.result)

        try:
            self.action_executor.run()
            self.is_running = False
            self.evaluate_solution()
            self.event_process.close_event.trigger(self.result)
        except CompileException as ex:
            logger.info('compilation failed')
            self.is_running = False
            self.evaluate_solution()
            self.event_process.close_event.trigger(self.result)
            raise ex

        return self.result

    def _walk_cases(self):
        for case in self.cases:
            for subcase in case.cases():
                yield subcase.id, case, subcase

    def iter_subcases(self) -> typing.List[Subcase]:
        if self.subcases:
            for sc in self.subcases:
                yield sc
        else:
            self.subcases = list()
            for case in self.cases:
                for subcase in case.cases():
                    sc = Subcase(subcase.id, case, subcase, self.temp_dir, self.problem_dir)
                    self.subcases.append(sc)
                    yield sc

    def destroy(self):
        try:
            if self.action_executor:
                self.action_executor.destroy()
            else:
                logger.warning('cannot destroy empty action_executor')
        except:
            logger.exception('could not destroy executor')

    def evaluate_solution(self):
        if self.is_running:
            self.result.result.message = 'Processing'
            self.result.result.status = ExecutorStatus.RUNNING
            return

        if not self.result.results:
            self.result.result.status = ExecutorStatus.SKIPPED
            self.result.result.message = 'No tests to run'
            return

        statuses = [x.status for x in self.result.results]
        compilation = self.result.compilation
        if compilation and compilation.status in (ExecutorStatus.COMPILATION_FAILED, ExecutorStatus.GLOBAL_TIMEOUT):
            for test in self.result.results:
                if test is not compilation:
                    test.status = ExecutorStatus.SKIPPED

            statuses = [x.status for x in self.result.results]
            statuses.append(self.result.compilation.status)

        unique = set(statuses)
        max_status = max(unique)
        logger.info('statuses: {}', unique)

        self.result.result.status = max_status

        if self.action_executor:
            self.result.result.duration = self.action_executor.duration
            ok_score = statuses.count(ExecutorStatus.ANSWER_CORRECT)
            at_score = statuses.count(ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
            rest_statuses = (
                ExecutorStatus.ANSWER_CORRECT,
                ExecutorStatus.ANSWER_CORRECT_TIMEOUT,
                ExecutorStatus.OK,
            )
            wr_score = len([x for x in statuses if x not in rest_statuses])

            self.result.result.score = (
                (10**4) * ok_score +
                (10**2) * at_score +
                (10**0) * wr_score
            )
            self.result.result.scores = [ok_score, at_score, wr_score]

        status = self.result.result.status
        action = self.type
        if action is ProcessRequestType.SOLVE:
            self.result.result.message = status.message

        elif action is ProcessRequestType.GENERATE_INPUT:
            if status is ExecutorStatus.OK:
                self.result.result.message = 'Input files generated'
            else:
                self.result.result.message = status.message

        elif action is ProcessRequestType.GENERATE_OUTPUT:
            if status is ExecutorStatus.OK:
                self.result.result.message = 'Output files generated'
            else:
                self.result.result.message = status.message

    def save_result(self):
        if self.type is not ProcessRequestType.SOLVE:
            logger.warning('No need to save action type {} ', self.type)
            logger.warning('It is already saved in a problem directory: {}', self.problem_dir)
            return None, None

        import datetime
        format_dict = dict(
            problem=self.problem,
            course=self.course,
            user=self.user,
            lang=self.lang,
            status=self.result.result.status,
            datetime=datetime.datetime.now(),
        )

        student_base_dir = Env.results.joinpath(Env.student_dir_format.format(**format_dict))
        student_base_dir.mkdir(parents=True, exist_ok=True)
        results = list(student_base_dir.glob('*'))
        total_attempts = len(results)
        format_dict['attempt'] = attempt = total_attempts + 1

        # ---------------------------------------------------------------------

        student_version = Env.student_version_format.format(**format_dict)

        student_full_dir = student_base_dir.joinpath(student_version)
        logger.info('Saving result to {}', student_full_dir)

        if self.result_dir.exists():
            shutil.copytree(str(self.result_dir), student_full_dir)
        else:
            logger.warning('dir {} does not exists', self.result_dir)
        student_full_dir.mkdir(parents=True, exist_ok=True)

        # ---------------------------------------------------------------------

        results = list()
        for test in self.result.results:
            results.append(Env.student_result_test_txt_format.format(test=test))

        format_dict['results'] = '\n'.join(results)
        result_txt = Env.student_result_txt_format.format(**format_dict)
        student_full_dir.joinpath('result.txt').write_text(result_txt)
        logger.info('saving result.txt: \n{}', result_txt)
        return str(student_full_dir.relative_to(Env.root)), attempt

    def get_log_dict(self):
        doc = dict(
            user=self.user.id,
            action=self.type.value,
            course=self.course.id,
            problem=self.problem.id,
            docker=self.docker,
        )
        if self.lang:
            doc['language'] = self.lang.id
        if self.solution:
            doc['solution'] = self.solution

        return doc

    def get_result_dict(self):
        # base = self.get_log_dict()
        # if self._evaluation:
        #     base['result'] = self._evaluation.peek(full=False)
        #
        # if self._compile_result:
        #     base['compilation'] = self._compile_result.peek(full=False)
        #
        # if self._run_results:
        #     tests = list()
        #     for test in self._run_results:
        #         if test:
        #             tests.append(test.peek(full=False))
        #     base['tests'] = tests

        return self.result.peek(False)


def _configure_cmd(cmd, file):
    opts = dict(
        filename=os.path.basename(file),
        filepath=file,
        file=os.path.basename(file).split('.')[0],
    )
    cp = []
    for c in cmd:
        s = str(c).replace('<', '{').replace('>', '}')
        cp.append(s.format(**opts))
    return cp
