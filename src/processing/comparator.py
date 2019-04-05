#!/bin/python3
# author: Jan Hybs

from processing import ExecutorStatus
import utils.io as io


class Comparator(object):
    """
    :type result: ExecutorStatus
    """

    def __init__(self, result, message=None):
        self.result = result
        self.message = message

    @classmethod
    def compare_files(cls, f1, f2, keep_going=True):
        if f1 == f2:
            return Comparator(ExecutorStatus.ANSWER_CORRECT, list())

        error = list()
        output = list()
        result = True

        lines1 = io.read_file(f1).splitlines()
        lines2 = io.read_file(f2).splitlines()

        lenl1 = len(lines1)
        lenl2 = len(lines2)

        for i in range(max(lenl1, lenl2)):
            l1 = lines1[i] if i < lenl1 else '""'
            l2 = lines2[i] if i < lenl2 else '""'
            output.append(l2)

            if l1 != l2:
                error.extend([
                    'line %d error:' % (i + 1),
                    '     expected: %s' % l1,
                    '        found: %s' % l2,
                    ''
                ])
                result = False
                if not keep_going:
                    break

        if result:
            return Comparator(ExecutorStatus.ANSWER_CORRECT, error)
        else:
            return Comparator(ExecutorStatus.ANSWER_WRONG, error)

    def __bool__(self):
        return self.result in (
            ExecutorStatus.ANSWER_CORRECT,
        )

    def peek(self):
        return dict(
            result=self.result,
            message=self.message,
        )
