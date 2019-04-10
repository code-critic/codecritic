#!/bin/python3
# author: Jan Hybs
from utils.strings import ensure_iterable


class FatalException(Exception):
    def __init__(self, message, details=None):
        self.message = message
        self.details = ensure_iterable(details)
        super().__init__(self.message)

    def peek(self):
        return dict(
            message=self.message,
            details=self.details,
        )


class CompileException(Exception):
    def __init__(self, message, details=None):
        self.message = message
        self.details = ensure_iterable(details)
        super().__init__(self.message)

    def peek(self):
        return dict(
            message=self.message,
            details=self.details,
        )


class ConfigurationException(Exception):
    def __init__(self, message, details=None):
        self.message = '[visible to admin only] {}'.format(message)
        self.details = ensure_iterable(details)
        super().__init__(self.message)

    def peek(self):
        return dict(
            message=self.message,
            details=self.details,
        )