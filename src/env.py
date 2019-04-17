#!/bin/python3
# author: Jan Hybs

import pathlib
import subprocess
_root = pathlib.Path(pathlib.Path(__file__).parent.parent)
_head_command = ['git', 'log', '-1', '--date=relative', '--pretty=%h %ad %ae %s']


_result_txt_test_format = '[{test.status.name:^20s}] problem {test.id:<40s} {test.duration:6.3f} sec'
_result_txt_format = '''
course:         {course.year}/{course.name}
problem:        {problem.id}
student:        {user.id}
language:       {lang.version}
datetime:       {datetime:%Y-%m-%d %H-%M-%S}
attempt:        {attempt}.

{results}

Final evaluation {status.name}
'''.strip()


class _Env(object):
    """
    Internal config
    """
    input_dir_name = 'input'
    output_dir_name = 'output'
    error_dir_name = '.error'
    compile_log_name = '.compile.log'


class Env(object):
    """
    Public config
    """
    version = '0.1.0'
    root = _root
    src = _root / 'src'
    cfg = _root / 'cfg'
    www = _root / 'www'
    tmp = _root / '.tmp'
    log_file = _root / '.automate.log'
    backdoor = False

    courses = _root / 'courses'
    results = _root / 'results'

    fonts = _root / 'www' / 'fonts'

    openssl_secret = _root / '.openssl_secret'
    database_secret = _root / '.database_secret.yaml'

    # -------------------------------------------------------------------------

    problem_timeout = 60.0
    case_timeout = 5.0
    teacher_timeout = 60.0 * 10
    compile_timeout = 30.0

    # -------------------------------------------------------------------------

    # url_slave = 'http://hybs.nti.tul.cz:5000' # for testing only
    url_slave = 'http://flowdb.nti.tul.cz:5000'
    url_login = 'https://flowdb.nti.tul.cz/secure'
    url_logout = 'https://flowdb.nti.tul.cz/Shibboleth.sso/Logout'
    HEAD = subprocess.check_output(_head_command).decode()

    # -------------------------------------------------------------------------

    student_dir_format = '{course.results_dir}/{user.di}/{problem.id}'
    student_version_format = '{attempt:02d}-{status.value:03d}-{status.abbr}-{status.str}'
    student_result_txt_format = _result_txt_format
    student_result_test_txt_format = _result_txt_test_format

    # -------------------------------------------------------------------------

    @classmethod
    def secret_key(cls):
        return cls.openssl_secret.read_text().strip()

    @classmethod
    def database_config(cls):
        import yaml
        return yaml.load(cls.database_secret.read_text())

    @classmethod
    def info(cls):
        for k, v in cls.__dict__.items():
            if str(k).startswith('_'):
                continue
            if str(k).endswith('_format'):
                continue
            if str(k).endswith('_secret'):
                continue
            if isinstance(v, classmethod):
                continue

            yield k, v

