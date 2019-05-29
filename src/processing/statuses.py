#!/bin/python3
# author: Jan Hybs


from dataclasses import dataclass
from typing import Optional


@dataclass(order=True, frozen=True)
class ResultStatus:
    code: int
    name: str
    abbr: Optional[str] = ''
    message: Optional[str] = ''
    score: Optional[int] = 0

    def __getitem__(self, value):
        return getattr(self, value, None)


NO_STATUS = ResultStatus(999, '-')


class ResultStatusMeta(type):
    def __getitem__(cls, value) -> ResultStatus:
        for key, item in cls.__dict__.items():
            if value == key:
                return item

            if isinstance(item, ResultStatus):
                if item.name == value:
                    return item
                elif item.code == value:
                    return item
        return NO_STATUS

    def __call__(cls, *args, **kwargs) -> ResultStatus:
        return cls[args[0]]


class Status(object, metaclass=ResultStatusMeta):
    # good results
    IN_QUEUE = ResultStatus(
        name='in-queue',
        code=96,
        abbr='Q',
    )

    RUNNING = ResultStatus(
        name='running',
        code=97,
        abbr='R',
    )

    IGNORE = ResultStatus(
        name='ignore',
        code=98,
        abbr='I',
    )

    OK = ResultStatus(
        name='ok',
        code=99,
        abbr='O',
        message='OK',
    )

    # bad results
    ANSWER_CORRECT = ResultStatus(
        name='answer-correct',
        code=100,
        abbr='A',
        message='Submitted solution is correct',
        score=10**4,
    )

    ANSWER_CORRECT_TIMEOUT = ResultStatus(
        name='answer-correct-timeout',
        code=101,
        abbr='AT',
        message='Submitted solution is correct, but does not meet duration criteria',
        score=10**2,
    )

    ANSWER_WRONG = ResultStatus(
        name='answer-wrong',
        code=200,
        abbr='W',
        message='Submitted solution is wrong',
        score=10**0,
    )

    ANSWER_WRONG_TIMEOUT = ResultStatus(
        name='answer-wrong-timeout',
        code=201,
        abbr='WT',
        message='Submitted solution is wrong and does not meet duration criteria',
    )

    # even worse
    SKIPPED = ResultStatus(
        name='skipped',
        code=300,
        abbr='S',
        message='skipped',
    )

    SOFT_TIMEOUT = ResultStatus(
        name='soft-timeout',
        code=301,
        abbr='T',
        message='timeout',
    )

    # really bad ones
    GLOBAL_TIMEOUT = ResultStatus(
        name='global-timeout',
        code=400,
        abbr='T',
        message='Submitted solution did not finish in time',
    )

    FILE_NOT_FOUND = ResultStatus(
        name='file-not-found',
        code=401,
        abbr='X',
        message='Fatal error, file not found',
    )

    ERROR_WHILE_RUNNING = ResultStatus(
        name='error-while-running',
        code=402,
        abbr='X',
        message='There was an error while running',
    )

    COMPILATION_FAILED = ResultStatus(
        name='compilation-failed',
        code=403,
        abbr='X',
        message='There was an error during compilation',
    )

    @classmethod
    def get(cls, value) -> ResultStatus:
        return cls[value]
