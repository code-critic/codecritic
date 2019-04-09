#!/bin/python3
# author: Jan Hybs

import pathlib
import subprocess
from flask import Flask


root = pathlib.Path(__name__).resolve().parent.parent.parent
src = root / 'src'
cmd = 'python3 www/start.py'.split()

class Glob():
    process = None



Glob.process = subprocess.Popen(cmd, cwd=str(src))


app = Flask(__name__)
@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if Glob.process:
        Glob.process.kill()

    subprocess.Popen('git pull'.split(), cwd=str(root)).wait()
    Glob.process = subprocess.Popen(cmd, cwd=str(src))
    return 'ok'


# http://hybs.nti.tul.cz:5001/webhook
app.run(host='0.0.0.0', port=5001)