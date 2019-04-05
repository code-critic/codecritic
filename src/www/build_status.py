#!/bin/python3
# author: Jan Hybs


import urllib.request
import pathlib
import json
import io
from flask import Blueprint, send_file, Response
from PIL import Image, ImageDraw, ImageFont


fonts= '/home/jan-hybs/projects/automate/www/fonts'
fonts= '/var/www/html/fonts'
blueprint = Blueprint('status', __name__)
jenkins_url = 'http://ciflow.nti.tul.cz:8080'
colors = dict(
    RUNNING='#0172b2',
    SUCCESS='#769e00',
    FAILURE='#ca543e',
    UNSTABLE='#ad8b14',
    UNKNOWN='#999999',
    ABORTED='#999999',
)


class StatusShield(object):
    def __init__(self, jenkins_url=jenkins_url, colors=colors, fonts=fonts):
        self.jenkins_url = jenkins_url

        self.W, self.H = 500, 20
        self._set_agent()
        self.colors = colors
        self.ubuntu = ImageFont.truetype(str(pathlib.Path(fonts).joinpath('Ubuntu-R.ttf')), size=11)
        self.ubuntu_small = self.ubuntu.font_variant(size=10)

    def _draw_text(self, draw, text, x, y, fill=None, padding=5, font=None):
        if font is None:
            font = self.ubuntu

        w, h = draw.textsize(text, font=font)
        wmid, hmid = (self.W - w) / 2, (self.H - h) / 2
        if y == 'm':
            y = hmid - 1
        if x == 'm':
            x = wmid

        if fill:
            draw.rectangle([
                (x, 0),
                (x + w + padding * 2, self.H)
            ], fill=fill)

        # # shadow
        # draw.text((x + padding, y+1), text, fill=(0, 0, 0, 0), font=font)
        draw.text((x + padding, y), text, fill="white", font=font)
        return x + w + padding * 2, y + h

    def _serve_pil_image(self, pil_img):
        img_io = io.BytesIO()
        pil_img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png', cache_timeout=60)

    def _add_corners(self, im, rad, upscale=3):
        w, h = im.size
        rad = rad

        radius = rad * upscale
        W, H = w * upscale, h * upscale

        circle = Image.new('L', (W, H), 50)
        draw = ImageDraw.Draw(circle)
        draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=255)
        draw.pieslice((W - radius * 2, 0, W, radius * 2), 270, 360, fill=255)
        draw.pieslice((0, H - radius * 2, radius * 2, H), 90, 180, fill=255)
        draw.pieslice((W - radius * 2, H - radius * 2, W, H), 0, 90, fill=255)
        draw.rectangle((radius, radius, W - radius, H - radius), fill=255)
        draw.rectangle((radius, 0, W - radius, radius), fill=255)
        draw.rectangle((0, radius, radius, H - radius), fill=255)
        draw.rectangle((radius, H - radius, W - radius, H), fill=255)
        draw.rectangle((W - radius, radius, W, H - radius), fill=255)

        circle.thumbnail((w, h), Image.ANTIALIAS)
        im.putalpha(circle)
        return im

    def _load_last_statuses(self, job_name):
        # full_url = '{jenkins_url}/job/{job_name}/api/json?tree=builds[number,status,timestamp,id,result]'
        full_url = '{jenkins_url}/job/{job_name}/api/json?tree=builds[id,result]'.format(
            jenkins_url=self.jenkins_url,
            job_name=job_name
        )

        try:
            with urllib.request.urlopen(full_url) as url:
                data = json.loads(url.read().decode())
                for build in data['builds']:
                    result = build['result']
                    yield (result or 'RUNNING', '#' + build['id'])
        except:
            yield ('UNKNOWN', 'undetermined')

    def get_status(self, text, job_name, limit=5):
        statuses = list(self._load_last_statuses(job_name))[:limit][::-1]
        return self._serve_pil_image(
            self.generate_image_from_statuses(text, statuses)
        )

    def generate_image_from_statuses(self, text, statuses):
        """
        :rtype: PIL.Image.Image
        """
        img = Image.new('RGBA', size=(self.W, self.H), color='white')
        draw = ImageDraw.Draw(img)

        x, y = self._draw_text(draw, text, 0, 'm', fill='#555555', padding=5)

        for status, name in statuses:
            fill = self.colors.get(status, self.colors['UNKNOWN'])
            x, y = self._draw_text(draw, str(name), x+2, 'm', fill=fill, font=self.ubuntu_small, padding=3)
        img = img.crop((0, 0, x+1, self.H))

        img = self._add_corners(img, 3)
        return img

    @staticmethod
    def _set_agent():
        proxy = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy)
        opener.addheaders = [
            ('User-Agent',
             'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30'
             )
        ]
        urllib.request.install_opener(opener)


@blueprint.route('/<string:text>/<string:job_name>')
@blueprint.route('/<string:text>/<string:job_name>/<int:limit>')
def status_shield(text, job_name, limit=5):
    return StatusShield().get_status(text, job_name, limit)
