from time import time
from threading import RLock
from contextlib import contextmanager

TO_WRAP = set((
    'event',
    'gauge',
    'increment',
    'decrement',
    'histogram',
    'timing',
    'flush',
    ))

def nop(*args, **kwargs):
    pass

class NOPStats(object):

    def __getattr__(self, name):
        if name in TO_WRAP:
            return nop
        raise AttributeError('{} not in TO_WRAP'.format(name))

# TODO pls improve if you see a better way. this sucks
class WrappedStats(object):

    def __init__(self, unwrapped_stats):
        self.unwrapped_stats = unwrapped_stats
        self.lock = RLock()

    def __getattr__(self, name):
        if name in TO_WRAP:
            def wrapper(*args, **kwargs):
                with self.lock:
                    return getattr(self.unwrapped_stats, name)(*args, **kwargs)
            return wrapper
        raise AttributeError('{} not in TO_WRAP'.format(name))

    @contextmanager
    def timer(self, metric_name, sample_rate=1, tags=None, host=None):
        start = time()
        try:
            yield
        finally:
            end = time()
            with self.lock:
                # TODO TODO TODO *1000 is a hack. Datadog seems to generally operate in seconds, but we've been using ms in other places.
                self.unwrapped_stats.timing(
                    metric_name, (end - start)*1000, end,
                    tags=tags, sample_rate=sample_rate, host=host,
                    )

    def timed(self, metric_name, sample_rate=1, tags=None, host=None):
        def wrapper(func):
            @wraps(func)
            def wrapped(*args, **kwargs):
                with self.timer(metric_name, sample_rate, tags, host):
                    result = func(*args, **kwargs)
                    return result
            return wrapped
        return wrapper
