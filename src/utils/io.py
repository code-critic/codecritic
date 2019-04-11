#!/bin/python3
# author: Jan Hybs

import os
import time
import shutil
import pathlib
import subprocess

from loguru import logger

ONE_DAY = 60*60*24
HALF_DAY = 60*60*12


def delete_old_files(root: pathlib.Path, seconds=HALF_DAY):
    if root.name not in ('tmp', '.tmp'):
        logger.warning('Aborting deletion of old dirs: folder {} not named tmp', root)
        return False

    deleted = 0
    total = 0
    ts = int(time.time())
    for d in root.glob('*'):
        if d.is_dir():
            modif = int(os.path.getmtime(d))
            total += 1

            if (ts - modif) > seconds:
                try:
                    logger.debug('deletig old file {} ({:1.1f} days old)', d, (ts - modif) / ONE_DAY)
                    shutil.rmtree(str(d), ignore_errors=True)
                    deleted += 1
                except Exception as e:
                    logger.exception('Cannot delete dir %s' % d)

    logger.info('deleted {} out of {} old dirs', deleted, total)
    return deleted


def write_file(f, s, mode='w'):
    if f:
        os.makedirs(os.path.dirname(f), 0o777, True)
        if s is None:
            s = ''
        with open(f, mode) as fp:
            fp.write(s)


def read_file(f, mode='r'):
    if not f:
        return ''
    if not os.path.exists(f):
        return ''
    with open(f, mode) as fp:
        return fp.read()


def secure_open_file(f, mode='w'):
    if not os.path.exists(f):
        write_file(f, '')

    return open(f, mode)


def remove_file(f):
    try:
        os.unlink(f)
        return True
    except:
        return False


class FileEx(object):
    def __init__(self, sink=None, mode='w', autoremove=False):
        self._sink = sink
        self._fp = None
        self._is_opened = False
        self._open_func = lambda f: f
        self._close_func = lambda f, fp: f
        self._read_func = None
        self._remove_func = None
        self._content = ''
        self.autoremove = autoremove

        if self._sink is None:
            self._open_func = lambda f: None
            self._close_func = lambda f, fp: None

        elif self._sink in (subprocess.PIPE, subprocess.DEVNULL, subprocess.STDOUT):
            self._open_func = lambda f: f
            self._close_func = lambda f, fp: f

        elif isinstance(self._sink, str):
            self._open_func = lambda f: secure_open_file(f, mode)
            self._close_func = lambda f, fp: fp.close()
            self._read_func = lambda f: read_file(f)
            self._remove_func = lambda f: remove_file(f)

    def open(self):
        if not self._is_opened:
            self._is_opened = True
            self._fp = self._open_func(self._sink)
        return self._fp

    def close(self):
        if self._is_opened:
            self._is_opened = False
            self._close_func(self._sink, self._fp)
            self._fp = None

            if self.autoremove:
                self.remove_empty()

    def read(self):
        if self._content:
            return self._content

        if self._read_func:
            self._content = self._read_func(self._sink)
        return self._content

    def emtpy(self):
        return self._content == ''

    def remove_empty(self):
        if self._remove_func and self.emtpy():
            self._remove_func(self._sink)

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __repr__(self):
        return 'FileEx(%s)' % self._sink

    @property
    def path(self):
        if isinstance(self._sink, str):
            return self._sink
