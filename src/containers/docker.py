#!/bin/python3
# author: Jan Hybs

import subprocess as sp
import docker
import docker.models.containers
from docker import errors


class ContainerAPI(object):
    def __init__(self, container:docker.models.containers.Container):
        self.container = container

    def exec(self, cmds) -> str:
        return self.container.exec_run(cmds).output.decode()

    def _cp(self, src, dest, timeout=10):
        cmd = 'docker cp {src} {dest}'
        cmds = [x.format(src=src, dest=dest) for x in cmd.split()]
        process = sp.Popen(cmds)
        try:
            return process.wait(10)
        except Exception:
            return False

    def copy_from_container(self, src, dest, timeout=10):
        return self._cp(
            src='{name}:{src}'.format(name=self.container.name, src=src),
            dest=dest
        )

    def copy_to_container(self, src, dest, timeout=10):
        return self._cp(
            src=src,
            dest='{name}:{dest}'.format(name=self.container.name, dest=dest),
        )


class DockerAPI(object):
    _client = None
    _api = None

    @classmethod
    def client(cls):
        if not cls._client:
            cls._client = docker.from_env()
        return cls._client

    @classmethod
    def api(cls):
        if not cls._api:
            cls._api = docker.APIClient()
        return cls._api

    @classmethod
    def remove_container(cls, id_or_name, force=True):
        try:
            cls.api().remove_container(id_or_name, force=force)
            return True
        except errors.NotFound:
            return False

    @classmethod
    def get_container(cls, id_or_name):
        if not id_or_name:
            return None

        try:
            return ContainerAPI(cls.client().containers.get(id_or_name))
        except:
            return None

    @classmethod
    def create_container(cls, image, name=None, **kwargs) -> ContainerAPI:
        return cls.get_container(name) or ContainerAPI(cls.client().containers.run(image, detach=True, name=name, stdin_open=True, **kwargs))
