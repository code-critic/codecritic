#!/bin/python3
# author: Jan Hybs


class Event(object):
    """Event system class

    A list of callable objects. Calling an instance of this will cause a
    call to each item in the list in ascending order by index.

    """
    def __init__(self, name):
        self._events = list()
        self.name = name

    def __call__(self, *args, **kwargs):
        for f in self._events:
            f(*args, **kwargs)

    def __repr__(self):
        return "Event %s (%s)" % (self.name, self._events)

    def on(self, event):
        self._events.append(event)

    def off(self, event):
        self._events.remove(event)

    def trigger(self, *args, **kwargs):
        self(*args, **kwargs)


class MultiEvent(object):
    def __init__(self, name, open_name=None, close_name=None):
        self.open_event = Event('%s-%s' % (name, open_name if open_name else 'start'))
        self.close_event = Event('%s-%s' % (name, close_name if close_name else 'end'))
        self._target = None

    def on(self, open_event=None, close_event=None):

        if open_event:
            self.open_event.on(open_event)

        if close_event:
            self.close_event.on(close_event)

    def off(self, open_event=None, close_event=None):
        if open_event:
            self.open_event.off(open_event)

        if close_event:
            self.close_event.off(close_event)

    def trigger(self, *args, **kwargs):
        self.open_event.trigger(*args, **kwargs)
        self.close_event.trigger(*args, **kwargs)

    def target(self, *targets):
        self._target = targets
        return self

    def __enter__(self):
        self.open_event.trigger(*self._target)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_event.trigger(*self._target)
        return False
