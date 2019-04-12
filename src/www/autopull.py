#!/bin/python3
# author: Jan Hybs

import subprocess

from loguru import logger
from flask import Flask
from env import Env
import sys

src = Env.root / 'src'
cmd = [sys.executable, 'www/start.py', '--host', '0.0.0.0']
app = Flask(__name__)


class Glob():
    process = None


def restart_server():
    if Glob.process:
        Glob.process.kill()

    logger.info('starting server')
    Glob.process = subprocess.Popen(cmd, cwd=str(src))


def update_repo():
    cmds = [
        'git fetch --all',
        'git reset --hard origin/master',
    ]
    result = 0
    logger.info('updating main repo')
    for cmd in cmds:
        result = subprocess.Popen(cmd.split(), cwd=str(Env.root)).wait()
        print(cmd, result)
    return result == 0


def update_subrepos():
    result = 0
    for course in Env.courses.glob('*'):
        if course.is_dir():
            cwd = str(course)
            cmds = [
                'git fetch --all',
                'git reset --hard origin/master',
            ]
            logger.info('updating submodule {}', cwd)
            for cmd in cmds:
                result = subprocess.Popen(cmd.split(), cwd=cwd).wait()
                print(cmd, result)
    return result == 0


@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    result = update_subrepos()

    if not result:
        return 'failed, {}'.format(result)

    return 'ok, pull result = {}'.format(result)


@app.route('/webhook/full', methods=['POST', 'GET'])
def webhook_full():
    if Glob.process:
        Glob.process.kill()

    result = update_repo()
    if not result:
        restart_server()
        return 'failed, {}'.format(result)

    result = update_subrepos()
    if not result:
        restart_server()
        return 'failed, {}'.format(result)

    Glob.process = subprocess.Popen(cmd, cwd=str(src))
    return 'ok, pull result = {}'.format(result)



update_repo()
update_subrepos()
restart_server()

# http://hybs.nti.tul.cz:5001/webhook
app.run(host='0.0.0.0', port=5001)
