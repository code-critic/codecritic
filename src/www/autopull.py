#!/bin/python3
# author: Jan Hybs

import subprocess

from flask import Flask
from env import Env
import sys

src = Env.root / 'src'
cmd = [sys.executable, 'www/start.py']


update_repo = [
    'git fetch --all'
    'git reset --hard origin/master'
]



class Glob():
    process = None


Glob.process = subprocess.Popen(cmd, cwd=str(src))


app = Flask(__name__)
@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if Glob.process:
        Glob.process.kill()

    result = None
    for reset_cmd in update_repo:
        result = subprocess.Popen(reset_cmd.split(), cwd=str(Env.root)).wait()
        print(reset_cmd, result)
        if result != 0:
            sys.exit(1)

    Glob.process = subprocess.Popen(cmd, cwd=str(src))
    return 'ok, pull result = {}'.format(result)


# http://hybs.nti.tul.cz:5001/webhook
app.run(host='0.0.0.0', port=5001)
