import time
import logging
from queue import Queue
from threading import Lock
from collections import deque
from contextlib import contextmanager

# These will be used in multiple threads

class RateLimiter(object):

    def __init__(self, requests_per_second):
        """
        :param requests_per_second: number of requests per second
        """
        # multiply by 3 because RateLimiter limits the rate of calls of BaseWorker.fetch_document()
        # BaseWorker.fetch_document() makes approx 3 requests per call
        self.wait_period = 1.0 / float(requests_per_second)
        self.last_request = time.time()
        self.lock = Lock()
        self.logger = logging.getLogger(__name__).getChild(repr(self))

    @contextmanager
    def guard(self):
        with self.lock:
            time_since_last_request = time.time() - self.last_request
            if (time_since_last_request < self.wait_period):
                sleep_time = self.wait_period - time_since_last_request
                self.logger.debug("sleeping for {} seconds".format(sleep_time))
                time.sleep(sleep_time)
            self.last_request = time.time()
        yield
        pass


class ConcurrencyLimiter(object):

    def __init__(self, max_running):
        '''
            max_running: positive int

            Guard blocks of code in multiple threads to ensure that more than
            'max_running' blocks will be running at once.
            > limiter = ConcurrencyLimiter(...)
            >
            > # in threads
            > with limiter.guard():
            >     # block that is to be concurrency limited
        '''

        self.num_running = 0
        self.max_running = max_running
        self.waiting = deque()
        self.lock = Lock()

    @contextmanager
    def guard(self):
        self.lock.acquire()
        if self.num_running < self.max_running:
            self.num_running += 1
            self.lock.release()
        else:
            bucket = Queue()
            self.waiting.append(bucket)
            self.lock.release()
            bucket.get()
        yield
        with self.lock:
            if len(self.waiting) > 0:
                self.waiting.popleft().put(None)
            else:
                self.num_running -= 1
