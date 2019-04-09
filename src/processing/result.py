#!/bin/python3
# author: Jan Hybs
from processing import ExecutorStatus
from utils.crypto import sha1
from utils.strings import ensure_iterable


class ExecutorResult(object):
    def __init__(self, cmd, status=ExecutorStatus.IN_QUEUE, returncode=None, error=None):
        self.cmd = cmd
        self.status = status
        self.returncode = returncode
        self.error = error
        self.uuid = None
        self.id = None

        self.duration = 0

        self.stdinn = None
        self.stdout = None
        self.stderr = None
        self.message = None
        self.message_details = None
        self.console = None
        self.attachments = list()

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
        return 'Result([%s] => %s (%s) in %1.3f sec)' % (
            ' '.join(self.cmd),
            str(self.returncode),
            self.status.name,
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
                stdin=ensure_iterable(self.stdinn)[:100],
                stdout=ensure_iterable(self.stdout)[:100],
                stderr=ensure_iterable(self.stderr)[:100],
                console=ensure_iterable(self.console)[:100],
                message=self.message,
                message_details=ensure_iterable(self.message_details)[:100],
                attachments=ensure_iterable(self.attachments),
            )

        doc = dict(
            id=self.id,
            status=self.status.str,
            cmd=' '.join(ensure_iterable(self.cmd)),
            duration=self.duration,
            returncode=self.returncode,
            message=self.message,
            message_details=ensure_iterable(self.message_details),
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
