import traceback
from io import StringIO

class ScraperException(Exception):
    """Scraper-related exception"""

class ScraperConnectionException(ScraperException):
    """Connection error with server"""

class ScraperBadTorExitException(ScraperException):
    """Exit node is bad in some way"""

class ScraperUnexpectedException(ScraperException):
    """Circumstances we didn't forsee"""

class ScraperUnexpectedFlowException(ScraperUnexpectedException):
    """Odd HTTP interaction with server"""

class ScraperUnexpectedOtherException(ScraperUnexpectedException):
    """Generic exception we have to investigate"""

    def __init__(self, ex, *args):
        super().__init__(ex, *args)
        self.ex = ex

    def show(self):
        f = StringIO()
        traceback.print_tb(self.ex.__traceback__, file=f)
        return '{}\n{}'.format(f.getvalue(), repr(ex))
