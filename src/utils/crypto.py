#!/bin/python3
# author: Jan Hybs
import base64
import json
import hashlib

from Crypto.Cipher import AES


class SimpleCrypto(object):
    def __init__(self, secret_key, iv=None, mode=AES.MODE_CBC):
        self.secret_key = secret_key
        self.iv = iv or secret_key
        self.mode = mode
        self._block_size = len(secret_key)
        self._padding = ' '

    def pad(self, s):
        return s + (self._block_size - len(s) % self._block_size) * self._padding

    @property
    def new(self):
        return AES.new(
            key=self.secret_key,
            mode=self.mode,
            IV=self.iv
        )

    def encrypt(self, text):
        return base64.b64encode(
            self.new.encrypt(
                self.pad(str(text))
            )
        ).decode().replace('/', ':')

    def decrypt(self, text):
        return self.new.decrypt(
            base64.b64decode(
                str(text).replace(':', '/')
            )
        ).decode().rstrip(self._padding)

    def encrypt_json(self, obj, json=json):
        text = json.dumps(obj)
        return self.encrypt(text)

    def decrypt_json(self, text, json=json):
        return json.loads(self.decrypt(text))

    def __repr__(self):
        return '{self.__class__.__name__}(key={self.secret_key}, iv={self.iv}, {self.new})'.format(self=self)


def sha1(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()
