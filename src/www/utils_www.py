#!/bin/python3
# author: Jan Hybs

import os
import io
import collections
import pathlib

from env import Env

from flask import send_file
from flask_autoindex import AutoIndex
from utils.strings import string_hash
from www import app, login_required, admin_required, url_for


class Link(object):
    def __init__(self, url, text, tooltip=None):
        self.url = url
        self.text = text
        self.tooltip = tooltip or text

    @classmethod
    def CoursesBtn(cls):
        return cls(url_for('view_courses'), 'Courses', 'Go to course selection')

    @classmethod
    def CourseBtn(cls, course):
        return cls(
            url_for('view_course', course_name=course.name, course_year=course.year),
            course.name,
            'Go to course %s' % course.name
        )

    @classmethod
    def ProblemBtn(cls, course, problem):
        return cls(
            url_for('view_result', course_name=course.name, course_year=course.year, problem_id=problem.id),
            problem.name,
            'View Results of %s' % problem.name
        )


class Breadcrumbs(list):
    def add(self, url, text, tooltip=None):
        self.append(Link(url, text, tooltip))
        return self

    @classmethod
    def new(cls, *items):
        this = Breadcrumbs()
        for item in items:
            this.append(item)
        return this


ai = AutoIndex(app, browse_root=Env.courses, add_url_rules=False)


def serve_pil_image(pil_img):
    img_io = io.BytesIO()
    pil_img.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')


def generate_img(name, year):
    from PIL import Image, ImageDraw, ImageFont

    W, H = 284, 180

    colors = ['#f58220', '#89160f', '#0f8935', '#0f2689', '#530f89']
    idx = string_hash('%s-%s' % (name, year)) % len(colors)

    img = Image.new('RGB', (W, H), color=colors[idx])
    d = ImageDraw.Draw(img)
    ubuntu = ImageFont.truetype(os.path.join(Env.fonts, 'Ubuntu-B.ttf'))
    ubuntu_72 = ubuntu.font_variant(size=72)
    ubuntu_36 = ubuntu.font_variant(size=36)

    w, h = d.textsize(name, font=ubuntu_72)
    h1 = h
    d.text(((W - w) / 2, (H - h) / 2 - 40), name, fill="white", font=ubuntu_72)

    w, h = d.textsize(year, font=ubuntu_36)
    d.text(((W - w) / 2, (H - h) / 2 - 50 + h1), year, fill="white", font=ubuntu_36)
    return img


def register_routes(app, socketio):
    @app.route('/placeholder/<string:name>/<string:year>')
    @app.route('/placeholder/<string:name>/<string:year>/<int:scale>')
    def placeholder(name, year, scale=100):
        if scale == 100:
            return serve_pil_image(generate_img(name, year))
        else:
            from PIL import Image
            scale = scale / 100.0
            img = generate_img(name, year)
            W, H = img.size
            w, h = int(W*scale), int(H*scale)
            img = img.resize((w,h), Image.ANTIALIAS)
            return serve_pil_image(img)


    @app.route('/browse/<path:path>')
    @app.route('/browse/')
    @login_required
    @admin_required
    def autoindex(path='.'):
        return ai.render_autoindex(path)


    @app.route('/results/<path:path>')
    @login_required
    @admin_required
    def view_results_from_dir(path='.'):
        path = Env.root.joinpath(path) / 'result.txt'
        try:
            return send_file(str(path), mimetype='text/plain', attachment_filename='result.txt')
        except:
            return 'no such file'
