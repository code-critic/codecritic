#!/bin/python3
# author: Jan Hybs
import argparse
import sys
from loguru import logger
logger.configure(handlers=[dict(sink=sys.stdout)])

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--help', action='help', default=argparse.SUPPRESS,
        help=argparse._('show this help message and exit'))

flask_server = parser.add_argument_group('flask server')
flask_server.add_argument('-p', '--port', type=int, default=5000)
flask_server.add_argument('-h', '--host', type=str, default='0.0.0.0')
flask_server.add_argument('-d', '--debug', action='store_true')
args = parser.parse_args()


from www import app
from www import auth
from www import index
from www import course
from www import sockets
from www import utils_www
from env import Env

logger.info('Running automate version {}', Env.version)
logger.info('Listening on {host}:{port} (debug={debug})', **vars(args))
info = '\n'.join(['{:>20s}: {:s}'.format(k, str(v)) for k, v in Env.info()])
logger.info('Configuration in env.py:\n{}', info)


app.run(debug=args.debug, host=args.host, port=args.port)

#
#
# import json
# import pathlib
# from flask import Flask, send_file
# from PIL import Image, ImageDraw, ImageFont
# import urllib.request
#
#
# proxy = urllib.request.ProxyHandler({})
# opener = urllib.request.build_opener(proxy)
# opener.addheaders = [
#     ('User-Agent',
#      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30'
#      )
# ]
# urllib.request.install_opener(opener)
#
#
#
#
#
# app = Flask(__name__)
# jenkins_url = 'http://ciflow.nti.tul.cz:8080'
# url = 'https://img.shields.io/jenkins/s/http/ciflow.nti.tul.cz:8080/Flow123d-ci2runner-debug-multijob.png?style=flat-square&label=debug'
# # url = 'https://img.shields.io/badge/minified%20size-6.65%20kB-informational.png'
#
#
# def serve_pil_image(pil_img):
#     img_io = io.BytesIO()
#     pil_img.save(img_io, 'PNG')
#     img_io.seek(0)
#     return send_file(img_io, mimetype='image/png', cache_timeout=60)
#
#
# @app.route('/release')
# def status():
#     f, h = urllib.request.urlretrieve(url)
#     path = pathlib.Path(f)
#     print(f, h)
#     img = Image.open(path)
#     path.unlink()
#
#     return serve_pil_image(img)
#
#
# @app.route('/debug')
# def json_status():
#     job_name = 'Flow123d-ci2runner-debug-multijob'
#     job_name = 'test'
#     full_url = '{jenkins_url}/job/{job_name}/lastBuild/api/json'.format(
#         jenkins_url=jenkins_url,
#         job_name=job_name
#     )
#     full_url = '{jenkins_url}/job/{job_name}/api/json?tree=builds[number,status,timestamp,id,result]'.format(
#         jenkins_url=jenkins_url,
#         job_name=job_name
#     )
#
#     print(full_url)
#     with urllib.request.urlopen(full_url) as url:
#         data = json.loads(url.read().decode())
#         print(data)
#         building = data['building']
#         result = data['result']
#         print(building, result)
#
#     return full_url
#
#
# fonts = '/home/jan-hybs/projects/automate/www/fonts'
# ubuntu = ImageFont.truetype(str(pathlib.Path(fonts).joinpath('Ubuntu-B.ttf')), size=12)
# ubuntu_small = ubuntu.font_variant(size=10)
# W, H = 500, 20
# fills = dict(
#     RUNNING='#999999',
#     SUCCESS='#769e00',
#     FAILURE='#ca543e',
#     UNSTABLE='#ad8b14',
#     UNKNOWN='#999999',
#     ABORTED='#999999',
# )
#
#
# def draw_text(draw: ImageDraw, text, x, y, fill=None, padding=5, font=ubuntu):
#     w, h = draw.textsize(text, font=font)
#     wmid, hmid = (W - w) / 2, (H - h) / 2
#     if y == 'm':
#         y = hmid - 1
#     if x == 'm':
#         x = wmid
#
#     if fill:
#         draw.rectangle([
#             (x, 0),
#             (x + w + padding*2, H)
#         ], fill=fill)
#
#     draw.text((x+padding, y), text, fill="white", font=font)
#     return x + w + padding*2, y+h
#
#
# def load_last_statuses(job_name):
#     # full_url = '{jenkins_url}/job/{job_name}/api/json?tree=builds[number,status,timestamp,id,result]'.format(
#     full_url = '{jenkins_url}/job/{job_name}/api/json?tree=builds[id,result]'.format(
#         jenkins_url=jenkins_url,
#         job_name=job_name
#     )
#
#     with urllib.request.urlopen(full_url) as url:
#         data = json.loads(url.read().decode())
#         for build in data['builds']:
#             result = build['result']
#             yield (result or 'RUNNING', build['id'])
#
#
# @app.route('/status/<string:text>/<string:job_name>')
# @app.route('/status/<string:text>/<string:job_name>/<int:limit>')
# def foo(text, job_name, limit=5):
#     img = Image.new('RGBA', size=(W, H), color='white')
#     draw = ImageDraw.Draw(img)
#
#     x, y = draw_text(draw, text, 0, 'm', fill='#555555')
#
#     statuses = list(load_last_statuses(job_name))[:limit][::-1]
#     for status, number in statuses:
#         fill = fills.get(status, fills['UNKNOWN'])
#         print(status, number, fill)
#         x, y = draw_text(draw, '#%s' % number, x+2, 'm', fill=fill, font=ubuntu_small, padding=3)
#     img = img.crop((0, 0, x+1, H))
#     return serve_pil_image(img)
#
#
#
#
#
# from flask import Flask
# from www.build_status import blueprint
# app = Flask(__name__)
# app.register_blueprint(blueprint, url_prefix='/status/')
# app.run(host='0.0.0.0', debug=True)

# import PIL.ImageShow
# from PIL import Image, ImageDraw
#
# from www.build_status import StatusShield
# PIL.ImageShow.register(PIL.ImageShow.EogViewer, -1)
#
# status = StatusShield()
# im = status.generate_image_from_statuses('foo-bar-bar-bar', [('SUCCESS', '#1'), ('FAILURE', '#2')])
# im.show(command='eog')
