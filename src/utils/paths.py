#!/bin/python3
# author: Jan Hybs

import typing
from pathlib import Path


try:
    from env import _Env


    input_name = _Env.input_dir_name
    output_name = _Env.output_dir_name
    error_name = _Env.error_dir_name
except:
    input_name = 'input'
    output_name = 'output'
    error_name = '.error'


class IOEPaths(object):
    def __init__(self, root: Path, input_name=input_name, output_name=output_name, error_name=error_name):
        self.root = root

        self.relative_input = Path(input_name)
        self.relative_output = Path(output_name)
        self.relative_error = Path(error_name)

        self.input = self.root / self.relative_input
        self.output = self.root / self.relative_output
        self.error = self.root / self.relative_error

    def mkdir(self, mode=0o777, parents=True, exist_ok=True):
        self.input.mkdir(mode=mode, parents=parents, exist_ok=exist_ok)
        self.output.mkdir(mode=mode, parents=parents, exist_ok=exist_ok)
        self.error.mkdir(mode=mode, parents=parents, exist_ok=exist_ok)
        return self

    def ioe_files(self, filename: typing.Any):
        return IOEFiles(self, filename)

    def __repr__(self):
        return (
            'IOEPaths({self.root} '
            '[{self.relative_input}, '
            '{self.relative_output}, '
            '{self.relative_error}])'
        ).format(self=self)


class IOEFiles(object):
    def __init__(self, root: typing.Union[IOEPaths, Path], filename: typing.Any):
        self.root = root if isinstance(root, IOEPaths) else IOEPaths(root)
        self.filename = str(filename)
        self.input = self.root.input / self.filename
        self.output = self.root.output / self.filename
        self.error = self.root.error / self.filename

        self.relative_input = self.root.relative_input / self.filename
        self.relative_output = self.root.relative_output / self.filename
        self.relative_error = self.root.relative_error / self.filename

    def __repr__(self):
        return (
            'IOEFiles({self.root} '
            '[{self.relative_input}, '
            '{self.relative_output}, '
            '{self.relative_error}])'
        ).format(self=self)
