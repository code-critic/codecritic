#!/bin/python3
# author: Jan Hybs
import pathlib
import typing

from loguru import logger
from processing import ExecutorStatus, ProcessRequestType
from utils.crypto import sha1
from utils.strings import ensure_iterable


class RequestResult(object):
    """
    :type solution: typing.Optional[str]
    :type lang: typing.Optional[Languages]
    :type result: ExecutorResult
    :type results: typing.List[ExecutorResult]
    """
    def __init__(self, request):
        """
        :type request: processing.request.ProcessRequest
        """
        self.lang = request.lang
        self.solution = request.solution if request.solution else None
        self.docker = request.docker

        self.action = request.type
        self.user = request.user
        self.course = request.course
        self.problem = request.problem

        self.result = ExecutorResult.empty_result(ExecutorResult.RESULT)
        self.results = list()
        self.subcases = list(self._walk_cases())

        if self.action is ProcessRequestType.SOLVE:
            if self.lang.compile:
                self.results.append(ExecutorResult.empty_result(ExecutorResult.COMPILATION))
        else:
            p = self.problem.reference
            if p and p.lang_ref and p.lang_ref.compile:
                self.results.append(ExecutorResult.empty_result(ExecutorResult.COMPILATION))

        for subcase in self.subcases:
            self.results.append(ExecutorResult.empty_result(subcase.id))

    def _walk_cases(self):
        for case in self.problem.tests:
            for subcase in case.cases():
                yield subcase

    def __getitem__(self, id):
        for test in self.results:
            if test.id == id:
                return test

        if id is not ExecutorResult.COMPILATION:
            logger.warning('Could not find test {} in {}', id, self.results)

    def __setitem__(self, id, value):
        for i, test in enumerate(self.results):
            if test.id == id:
                self.results[i] = value
                return

        if id is not ExecutorResult.COMPILATION:
            logger.warning('Could not find test {} in {}', id, self.results)

    def __iter__(self):
        return iter(self.subcases)

    @property
    def compilation(self):
        return self[ExecutorResult.COMPILATION]

    @compilation.setter
    def compilation(self, value):
        self[ExecutorResult.COMPILATION] = value

    def peek(self, full=True):
        return dict(
            lang=self.lang.id if self.lang else None,
            solution=self.solution,
            docker=self.docker,

            action=self.action.value,
            user=self.user.id,
            course=self.course.id,
            problem=self.problem.id,

            result=self.result.peek(full),
            results=[x.peek(full) for x in self.results],
        )


class ExecutorResult(object):
    """
    :type stdin: pathlib.Path
    :type stdout: pathlib.Path
    :type stderr: pathlib.Path
    """
    COMPILATION = 'Compilation'
    RESULT = 'Result'

    def __init__(self, cmd=None, status=ExecutorStatus.IN_QUEUE, returncode=None, error=None):
        self.cmd = cmd
        self.status = status
        self.returncode = returncode
        self.error = error
        self.uuid = None
        self.id = None

        self.duration = 0

        self.message = None
        self.message_details = None
        self.console = None
        self.attachments = list()

        # score of the test
        self.score = 0
        self.scores = list()

        self.stdin = None
        self.stdout = None
        self.stderr = None

    @staticmethod
    def try_read(stream: pathlib.Path) -> typing.List[str]:
        try:
            return ensure_iterable(stream.read_text().splitlines())
        except:
            return []

    def read_stdout(self):
        return self.try_read(self.stdout)

    def read_stdin(self):
        return self.try_read(self.stdin)

    def read_stderr(self):
        return self.try_read(self.stderr)

    def register(self, id):
        self.id = id
        self.uuid = sha1(id)
        return self

    def add_attachment(self, *attachment: dict):
        self.attachments.extend(attachment)

    def __call__(self, status=None, returncode=None, error=None, duration=None):
        if status is not None:
            self.status = status

        if returncode is not None:
            self.returncode = returncode

        if error is not None:
            self.error = error

        if duration is not None:
            self.duration = duration

        return self

    def __repr__(self):
        return 'Result([%s], status=%s, rc=%s, duration=%1.3f)' % (
            self.id,
            self.status.name,
            str(self.returncode),
            self.duration
        )

    def failed(self):
        return self.returncode != 0

    def peek(self, full=True):
        if full:
            return dict(
                uuid=self.uuid,
                id=self.id,
                status=self.status.str,
                cmd=self.cmd,
                duration=self.duration,
                returncode=self.returncode,
                console=ensure_iterable(self.console)[:100],
                message=self.message,
                message_details=ensure_iterable(self.message_details)[:100],
                attachments=ensure_iterable(self.attachments),
                score=self.score,
                scores=self.scores,
            )

        doc = dict(
            id=self.id,
            status=self.status.str,
            cmd=' '.join(ensure_iterable(self.cmd)),
            duration=self.duration,
            returncode=self.returncode,
            message=self.message,
            message_details=ensure_iterable(self.message_details),
            score=self.score,
            scores=self.scores,
        )
        for p in ('cmd', 'message', 'message_details'):
            if p in doc and not doc[p]:
                doc.pop(p)
        return doc

    @classmethod
    def empty_result(cls, id, status=ExecutorStatus.IN_QUEUE):
        return ExecutorResult([], status).register(id)

    @classmethod
    def _showcase(cls):
        for status in ExecutorStatus:
            result = cls.empty_result(str(status), status)
            result.message = str(status)
            yield result
