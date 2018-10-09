#!/bin/python3
# author: Jan Hybs
import enum

import yaml

from cfg.requests import Request


class ResultStatus(enum.IntEnum):
    EMPTY = -2
    SKIPPED = -1
    ANSWER_OK = 0
    TIMEOUT_ANSWER_OK = 1

    ANSWER_WRONG = 2
    TIMEOUT_ANSWER_WRONG = 3

    EXECUTE_OK = 4
    EXECUTE_ERROR = 5

    COMPILE_OK = 6
    COMPILE_ERROR = 7

    GLOBAL_TIMEOUT = 8


class RequestResult(object):
    class TestResult(object):
        def __init__(self):
            self.result = ResultStatus.SKIPPED
            self.error = None
            self.duration = None

        def to_dict(self):
            return dict(
                result=self.result.name,
                error=self.error,
                duration=self.duration,
                code=self.result.value,
            )

    def __init__(self, request: Request):
        self.request = request
        self.compilation = RequestResult.TestResult()
        self.source_code = request.source_code

        self.tests = dict()
        for test in request.tests:
            self.tests[test.id] = RequestResult.TestResult()

    @property
    def result(self):
        if self.compilation.result in (ResultStatus.SKIPPED, ResultStatus.COMPILE_OK):
            return self.solution
        return self.compilation.result

    @property
    def solution(self):
        codes = {v.result for k, v in self.tests.items()}
        # codes = {
        #     ResultStatus.ANSWER_OK,
        #     ResultStatus.TIMEOUT_ANSWER_OK,
        #     ResultStatus.GLOBAL_TIMEOUT,
        #     ResultStatus.SKIPPED,
        # }

        if not codes:
            return ResultStatus.EMPTY

        # remove GLOBAL_TIMEOUT statuses
        codes.discard(ResultStatus.GLOBAL_TIMEOUT)

        if not codes:
            # if the set is empty
            # it means that we did not get past the first test
            return ResultStatus.GLOBAL_TIMEOUT

        return max(codes)

    def to_dict(self):
        main_result = self.result
        result = dict(
            user=self.request.user,
            lang=self.request.lang.id,
            prob=self.request.prob.id,
            result=main_result.name,
            code=main_result.value,
            compilation=self.compilation.to_dict(),
            tests=list(),
            # src=self.source_code,
        )

        for test in self.request.tests:
            test_dict = self.tests[test.id].to_dict()
            test_dict['id'] = test.id
            result['tests'].append(test_dict)

        return result

    def to_yaml(self):
        return yaml.dump(self.to_dict(), default_flow_style=False)

    def __repr__(self):
        return str(self.__dict__)
