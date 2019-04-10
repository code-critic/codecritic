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


Glob.process = subprocess.Popen(cmd, cwd=str(src))


app = Flask(__name__)
@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if Glob.process:
        Glob.process.kill()

    result = subprocess.Popen('git pull'.split(), cwd=str(Env.root)).wait()
    Glob.process = subprocess.Popen(cmd, cwd=str(src))
    return 'ok, pull result = {}'.format(result)


# http://hybs.nti.tul.cz:5001/webhook
app.run(host='0.0.0.0', port=5001)
