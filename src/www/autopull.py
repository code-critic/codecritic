#!/bin/python3
# author: Jan Hybs

import subprocess

from flask import Flask
from env import Env
import sys

src = Env.root / 'src'
cmd = [sys.executable, 'www/start.py']


class Glob():
    process = None


def update_repo():
    cmds = [
        'git fetch --all',
        'git reset --hard origin/master',
    ]
    result = None
    for cmd in cmds:
        result = subprocess.Popen(cmd.split(), cwd=str(Env.root)).wait()
        print(cmd, result)
        if result != 0:
            sys.exit(1)
    return result



app = Flask(__name__)
@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if Glob.process:
        Glob.process.kill()

    result = update_repo()
    Glob.process = subprocess.Popen(cmd, cwd=str(src))
    return 'ok, pull result = {}'.format(result)




update_repo()
Glob.process = subprocess.Popen(cmd, cwd=str(src))

# http://hybs.nti.tul.cz:5001/webhook
app.run(host='0.0.0.0', port=5001)
