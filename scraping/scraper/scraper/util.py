import codecs
import logging
from contextlib import contextmanager

# The pipes have ears (and many states have root certs in your browser)
def deobfuscate(interesting_string_that_is_obfuscated):
    return codecs.encode(interesting_string_that_is_obfuscated, encoding='rot13')


class NameFilter(logging.Filter):
    '''Filter loggers that do not start with the given prefix'''

    def __init__(self, names):
        self.names = names

    def filter(self, record):
        for name in self.names:
            if record.name.startswith(name):
                return True
        return False

@contextmanager
def nullcontext():
    yield
