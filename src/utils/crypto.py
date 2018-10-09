#!/bin/python3
# author: Jan Hybs
import base64
import json

from Crypto.Cipher import AES

from utils.strings import random_string


class SimpleCrypto(object):
    def __init__(self, secret_key=None):
        if not secret_key:
            secret_key = random_string(32)

        self.secret_key = secret_key

    def encrypt_json(self, obj):
        return self.encrypt(json.dumps(obj))

    def decrypt_json(self, text):
        return json.loads(self.decrypt(text))

    def encrypt(self, text):
        text += ((16 - len(text) % 16) * ' ')
        cipher = AES.new(self.secret_key, AES.MODE_ECB)
        return base64.b64encode(cipher.encrypt(text)).decode().replace('/', ':')

    def decrypt(self, text):
        cipher = AES.new(self.secret_key, AES.MODE_ECB)
        return cipher.decrypt(base64.b64decode(text.replace(':', '/'))).decode()

    def __repr__(self):
        return '{self.__class__.__name__}(key={self.secret_key})'.format(self=self)

crypto = SimpleCrypto('VVDYPU5A:DSMI9$PTXONN5@LVPP72ZR1')