from threading import RLock

import logging
import sys
import threading

class CodeTracker:

    def __init__(self, start_index, code_range, large_prime=32452867):
        """
        large_prime places an order on the elements of code_range (including the boundary points) from 0
        to end_code - start_code. start_index is a number in this second range that determines where the crawl begins.
        """
        self.start_code = code_range[0]
        self.end_code = code_range[1]
        self.size_range = self.end_code - self.start_code + 1
        self.large_prime = large_prime
        self.error_codes = []
        self.code_index = start_index
        self.lock = RLock()
        self.logger = logging.getLogger(__name__).getChild(repr(self))

    def next_code(self):
        """
            Next article code to be fetched
        """
        with self.lock:
            if len(self.error_codes) != 0:
                return self.error_codes.pop(0)
            else:
                if self.code_index >= self.size_range:
                    self.logger.debug("CRAWL FINISHED ON THREAD {}: ({}, {})".format(threading.get_ident(), self.start_code, self.end_code))
                    sys.exit(0)
                next_code = self.start_code + ((self.large_prime * self.code_index) % self.size_range)
                self.code_index = self.code_index + 1
                self.logger.debug("Code position: {}".format(self.code_index))
                return next_code

    def put_error(self, code):
        with self.lock:
            self.error_codes.append(code)
