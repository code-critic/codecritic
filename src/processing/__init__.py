#!/bin/python3
# author: Jan Hybs
import enum


class ExecutorStatus(enum.IntEnum):

    # system results
    IN_QUEUE = 96
    RUNNING = 97
    IGNORE = 98

    # good results
    OK = 99
    ANSWER_CORRECT = 100
    ANSWER_CORRECT_TIMEOUT = 101

    # bad results
    ANSWER_WRONG = 200
    ANSWER_WRONG_TIMEOUT = 201

    # even worse
    SKIPPED = 300
    SOFT_TIMEOUT = 301

    # really bad one
    GLOBAL_TIMEOUT = 400
    FILE_NOT_FOUND = 401
    ERROR_WHILE_RUNNING = 402
    COMPILATION_FAILED = 403

    @property
    def abbr(self):
        return {
            self.IN_QUEUE: 'Q',
            self.RUNNING: 'R',
            self.IGNORE: 'S',

            self.OK: 'O',
            self.ANSWER_CORRECT: 'A',
            self.ANSWER_CORRECT_TIMEOUT: 'AT',

            self.ANSWER_WRONG: 'W',
            self.ANSWER_WRONG_TIMEOUT: 'WT',

            self.SKIPPED: 'S',
            self.SOFT_TIMEOUT: 'T',

            self.GLOBAL_TIMEOUT: 'T',
            self.FILE_NOT_FOUND: 'X',
            self.ERROR_WHILE_RUNNING: 'X',
            self.COMPILATION_FAILED: 'X',
        }.get(self)

    @property
    def message(self):
        return {
            self.IN_QUEUE: 'in queue',
            self.RUNNING: 'is running',
            self.IGNORE: 'skipped',

            self.OK: 'OK',
            self.ANSWER_CORRECT: 'Submitted solution is correct',
            self.ANSWER_CORRECT_TIMEOUT: 'Submitted solution is correct, but does not meet duration criteria',

            self.ANSWER_WRONG: 'Submitted solution is wrong',
            self.ANSWER_WRONG_TIMEOUT: 'Submitted solution is wrong and does not meet duration criteria',

            self.SKIPPED: 'skipped',
            self.SOFT_TIMEOUT: 'timeout',

            self.GLOBAL_TIMEOUT: 'Submitted solution did not finish in time',
            self.FILE_NOT_FOUND: 'Fatal error, file not found',
            self.ERROR_WHILE_RUNNING: 'There was an error while running',
            self.COMPILATION_FAILED: 'There was an error during compilation',
        }.get(self)

    @property
    def str(self):
        return self.name.replace('_', '-').lower()

    def __repr__(self):
        return '<{self.__class__.__name__}.{self.name}: {self.str}({self.value})>'.format(self=self)


class ProcessRequestType(enum.Enum):
    GENERATE_OUTPUT = 'generate-output'
    GENERATE_INPUT = 'generate-input'
    SOLVE = 'solve'


docker_bash_template = '''
#!/bin/bash
cd {tmp_dir}
START=$(python3 -c "import time; print(time.time())")
{timeout_args} {pipeline_args} {in_name} {out_name} {err_name}
echo $?
END=$(python3 -c "import time; print(time.time())")
echo $START
echo $END
'''.lstrip()