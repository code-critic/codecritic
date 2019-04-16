#!/bin/python3
# author: Jan Hybs
import datetime
import os
import pathlib
import shutil
import typing

OptionalPath = typing.Optional[pathlib.Path]


from exceptions import FatalException, CompileException, ConfigurationException
from utils.crypto import b64encode
from collections import OrderedDict, namedtuple
from uuid import uuid4

from loguru import logger

from database.objects import Course, Courses, Languages, Problem, User, ProblemCase
from env import Env
from processing import ExecutorStatus, ProcessRequestType
from processing.result import ExecutorResult
from utils.events import MultiEvent
from utils.io import delete_old_files


def hook_warn_empty_input(id, result: ExecutorResult):
    if not result.stdin:
        raise FatalException('Input file is empty', ['please double check your input files for test', id])
    return result

def add_cmd_to_result(id, result: ExecutorResult):
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

        self.temp_stdin = self.temp_dir / 'input' / subcase.id
        self.temp_stdout = self.temp_dir / 'output' / subcase.id
        self.temp_stderr = self.temp_dir / '.error' / subcase.id

        self.problem_stdin = self.problem_dir / 'input' / subcase.id
        self.problem_stdout = self.problem_dir / 'output' / subcase.id
        self.problem_stderr = self.problem_dir / '.error' / subcase.id


class ProcessRequest(object):
    """
    :type _compile_result: ExecutorResult
    :type _run_results: OrderedDict[str, ExecutorResult]
    :type course: Course
    :type problem: Problem
    :type lang: Languages
    :type user: User
    :type action_executor: processing.actions.AbstractAction
    """

    def __init__(self, user, lang, type, solution, course, problem, cases=None, docker=True, **kwargs):
        self.course = Courses()[course]
        self.problem = self.course.problem_db[problem]
        self.lang = Languages.db().get(lang)
        self.case_ids = cases or self.problem.test_ids
        self.cases = self.problem.tests_from_ids(self.case_ids)
        self.datetime = datetime.datetime.now()

        self.user = user
        self.solution = solution
        self.type = ProcessRequestType(type)

        self.rand = '%s-%s' % (self.user.id, uuid4())
        self.uuid = uuid4().hex
        # self.rand = 'jan.hybs-c45ea043-15ae-4c3b-9c5d-352bc8cd5937'

        self._compile_result = None
        self._evaluation = ExecutorResult.empty_result(id='evaluation')
        self._run_results = OrderedDict()
        self.rest = kwargs
        self._subcases = None

        self.event_process = MultiEvent('on-process')

        self.event_compile = MultiEvent('on-compile')
        self.event_execute = MultiEvent('on-execute')

        self.event_compare_test = MultiEvent('on-compare-test')
        self.event_execute_test = MultiEvent('on-execute-test')
        self.running = False
        self.docker = docker
        self.action_executor = None

        self.problem_dir = pathlib.Path(self.course.problems_dir, self.problem.id)
        self.result_dir = pathlib.Path(Env.tmp, self.rand)
        self.temp_dir = pathlib.Path(Env.tmp, self.rand)

        self.problem_input_dir = self.problem_dir.joinpath('input')
        self.problem_output_dir = self.problem_dir.joinpath('output')
        self.problem_error_dir = self.problem_dir.joinpath('.error')
        self.problem_dirs = (self.problem_output_dir, self.problem_input_dir, self.problem_error_dir)

        self.temp_input_dir = self.temp_dir.joinpath('input')
        self.temp_output_dir = self.temp_dir.joinpath('output')
        self.temp_error_dir = self.temp_dir.joinpath('.error')
        self.temp_dirs = (self.temp_input_dir, self.temp_output_dir, self.temp_error_dir)

        # create dirs, but they SHOULD ALREADY EXISTS
        for d in (self.problem_dirs + self.temp_dirs):
            d.mkdir(parents=True, exist_ok=True)

    def __repr__(self):
        return ('Request(\n'
                '  user={self.user.id}\n'
                '  course={self.course.name}\n'
                '  problem={self.problem.id}\n'
                '  language={self.lang}\n'
                '  type={self.type}\n'
                ')').format(self=self)

    def peek(self):
        return dict(
            uuid=self.uuid,
            user=self.user.id,
            course=self.course,
            lang=self.lang,
            prob=self.problem,
            action=self.type,
            evaluation=self._evaluation,
        )

    @property
    def result_list(self):
        return self._run_results.items()

    # ------------------------------------------

    def process(self):
        self._run_results = OrderedDict()
        for id, case, subcase in self._walk_cases():
            self[id] = ExecutorResult.empty_result(id=id)

        # no tests provided
        if not self._run_results:
            self.event_process.open_event.trigger(self, self._run_results)
            self.evaluate_solution()
            self.event_process.close_event.trigger(self, self._run_results)
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

        self.event_process.open_event.trigger(self, self._run_results)
        try:
            self.action_executor.run()
            self.evaluate_solution()
            self.event_process.close_event.trigger(self, self._run_results)
        except CompileException as ex:
            logger.info('compilation failed')
            self.evaluate_solution()
            self.event_process.close_event.trigger(self, self._run_results)
            raise ex

        return self._run_results

    def _walk_cases(self):
        for case in self.cases:
            for subcase in case.cases():
                yield subcase.id, case, subcase

    def __getitem__(self, id):
        return self._run_results[id]

    def __setitem__(self, id, value):
        self._run_results[id] = value

    def __iter__(self):
        return iter(self._walk_cases())

    def iter_subcases(self):
        if self._subcases:
            for sc in self._subcases:
                yield sc
        else:
            self._subcases = list()
            for case in self.cases:
                for subcase in case.cases():
                    sc = Subcase(subcase.id, case, subcase, self.temp_dir, self.problem_dir)
                    self._subcases.append(sc)
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
        if not self._run_results:
            self._evaluation = ExecutorResult(status=ExecutorStatus.SKIPPED).register('FINAL RESULT')
            self._evaluation.message = 'No tests to run'
            return

        statuses = [x.status for x in self._run_results.values()]
        if self._compile_result:
            if self._compile_result.status in (ExecutorStatus.COMPILATION_FAILED, ExecutorStatus.GLOBAL_TIMEOUT):
                for k, v in self._run_results.items():
                    self._run_results[k].status = ExecutorStatus.SKIPPED

            statuses = [x.status for x in self._run_results.values()]
            statuses.append(self._compile_result.status)

        unique = set(statuses)
        max_status = max(unique)

        self._evaluation = ExecutorResult(None, max_status).register('FINAL RESULT')

        if self.action_executor:
            self._evaluation.duration = self.action_executor.duration
            print(statuses)
            ok_score = statuses.count(ExecutorStatus.ANSWER_CORRECT)
            at_score = statuses.count(ExecutorStatus.ANSWER_CORRECT_TIMEOUT)
            wr_score = statuses.count(ExecutorStatus.ANSWER_WRONG)
            rest_statuses = (ExecutorStatus.ANSWER_CORRECT, ExecutorStatus.ANSWER_CORRECT_TIMEOUT, ExecutorStatus.ANSWER_WRONG)
            rest = [x for x in statuses if x not in rest_statuses]

            self._evaluation.score = (
                (10**4) * ok_score +
                (10**2) * at_score +
                (10**0) * wr_score
            )
            self._evaluation.scores = [ok_score, at_score, wr_score]

        status = self._evaluation.status
        action = self.type
        if action is ProcessRequestType.SOLVE:
            self._evaluation.message = status.message

        elif action is ProcessRequestType.GENERATE_INPUT:
            if status is ExecutorStatus.OK:
                self._evaluation.message = 'Input files generated'
            else:
                self._evaluation.message = status.message

        elif action is ProcessRequestType.GENERATE_OUTPUT:
            if status is ExecutorStatus.OK:
                self._evaluation.message = 'Output files generated'
            else:
                self._evaluation.message = status.message

    def save_result(self):
        if self.type is not ProcessRequestType.SOLVE:
            logger.warning('No need to save action type {} ', self.type)
            logger.warning('It is already saved in a problem directory: {}', self.problem_dir)
            return None, None

        format_dict = dict(
            problem=self.problem,
            course=self.course,
            user=self.user,
            lang=self.lang,
            status=self._evaluation.status,
            datetime=self.datetime,
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
            shutil.copytree(self.result_dir, student_full_dir)
        else:
            logger.warning('dir {} does not exists', self.result_dir)
        student_full_dir.mkdir(parents=True, exist_ok=True)

        # ---------------------------------------------------------------------

        results = list()
        for id, test in self._run_results.items():
            results.append(Env.student_result_test_txt_format.format(test=test))

        format_dict['results'] = '\n'.join(results)
        result_txt = Env.student_result_txt_format.format(**format_dict)
        student_full_dir.joinpath('result.txt').write_text(result_txt)
        logger.info('saving result.txt: \n{}', result_txt)
        return str(student_full_dir.relative_to(Env.root)), attempt

    def get_log_dict(self):
        doc = dict(
            user=self.user.id,
            datetime=datetime.datetime.now(),
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
        base = self.get_log_dict()
        if self._evaluation:
            base['result'] = self._evaluation.peek(full=False)

        if self._compile_result:
            base['compilation'] = self._compile_result.peek(full=False)

        if self._run_results:
            tests = list()
            for id, test in self._run_results.items():
                if test:
                    tests.append(test.peek(full=False))
            base['tests'] = tests

        return base

    def _register_attachment(self, id, name, path: pathlib.Path):
        rel_path = str(path.relative_to(Env.root))
        self[id].add_attachment(dict(name=name+'.txt', path=rel_path))


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
