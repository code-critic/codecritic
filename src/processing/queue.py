#!/bin/python3
# author: Jan Hybs
import os

import yaml

from cfg.requests import Request
from processing.processor import Processor


class Queue(object):

    def __init__(self, folder):
        self.folder = folder
        self.requests = list()  # type: list[Request]

    def do_work(self):
        files = [os.path.join(self.folder, x) for x in os.listdir(self.folder) if x.endswith('.yaml')]
        self.requests = list()
        for f in files:
            with open(f, 'r') as fp:
                self.requests.append(Request(yaml.load(fp)))
        self.requests.sort(key=lambda x: x.priority, reverse=True)

        for request in self.requests:
            result = Processor.process_request(request)
            Processor.write_result(request, result)


