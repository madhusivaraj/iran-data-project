import re
import logging
import time
from io import BytesIO
from base64 import b64decode
from collections import namedtuple

from PIL import Image
from bs4 import BeautifulSoup
from requests import RequestException, ConnectionError

from scraper.session import is_old_url_for
from scraper.scheduler import wait_guard, mk_has_passed
from scraper.solve_captcha import solve_captcha
from scraper.exceptions import *

Result = namedtuple('Result', ('is_old', 'text'))

document_captcha_re = re.compile(r'(?P<path>/HttpHandler/Captcha.ashx\?w=(?P<w>[0-9]+)&h=(?P<h>[0-9]+)&c=(?P<c>[^&]+)&bc=(?P<bc>[0-9a-f]+)&rnd=(?P<rnd>[0-9]+))')

class Worker(object):

    def __init__(self, sess, global_ctx, ctx):
        '''
        Lifetime is that of the session.

        sess: A scraper.session.* object unique to this worker, for interacting with the website, possibly through a proxy.
        '''
        self.sess = sess
        self.global_ctx = global_ctx
        self.ctx = ctx
        self.logger = logging.getLogger(__name__).getChild(repr(self)) # different logger for each worker

    def fetch_document(self, code):
        '''
        Given an document code url parameter, try to get what's at the corresponding url by solving CAPTCHAs (after consulting the CAPTCHA cache).
        '''
        is_old = False
        resp = _check(self.sess.get_document, [200, 302], code)
        def if_right():
            pass
        def if_wrong():
            pass
        while True:
            if resp.status_code == 302:
                if is_old:
                    raise ScraperUnexpectedFlowException('redirected when already old for code={}'.format(code))
                if not is_old_url_for(code, resp.headers['location']):
                    raise ScraperUnexpectedFlowException('redirect to url other than old url of current url for code={}'.format(code))
                is_old = True
                resp = _check(self.sess.get_document, [200, 302], code, old=True)
            elif is_document_captcha_page(resp.text):
                with wait_guard(self.ctx.sched.captcha_time()):
                    if_wrong()
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    captcha_path = extract_document_captcha_path(soup)
                    solution, if_right, if_wrong = self.solve_captcha(captcha_path)
                    data = mk_document_captcha_form_data(soup, solution)
                resp = _check(self.sess.post_document, [200, 302], code, data, old=is_old)
            else:
                break
        with wait_guard(self.ctx.sched.document_time()):
            if is_present_document_page(resp.text):
                text = resp.text
            elif is_absent_document_page(resp.text):
                text = None
            else:
                raise ScraperUnexpectedException('unrecognized page type for code={}'.format(code))
            if_right()
            return Result(is_old=is_old, text=text)

    def solve_captcha(self, captcha_path):
        m = document_captcha_re.fullmatch(captcha_path)
        c = b64decode(m['c'])
        solution = self.ctx.captcha_cache.get(c)
        self.logger.debug('captcha cache returned %s for path %s', solution, captcha_path)
        if solution is not None:
            def if_right():
                self.ctx.stats.increment('captcha', tags={'cached': 'True', 'correct': 'True'})
            def if_wrong():
                self.logger.error('captcha was cached and wrong', solution, captcha_path)
                self.ctx.stats.increment('captcha', tags={'cached': 'True', 'correct': 'False'})
                self.ctx.captcha_cache.report_unexpected_incorrect(c, solution)
        else:
            resp = _check(self.sess.get_captcha, [200], captcha_path)
            im = Image.open(BytesIO(resp.content))
            with self.ctx.stats.timer('captcha_ocr_duration'):
                solution = solve_captcha(im)
            self.logger.debug('got solution %s for path %s', solution, captcha_path)
            def if_right():
                self.ctx.stats.increment('captcha', tags={'cached': 'False', 'correct': 'True'})
                self.ctx.captcha_cache.report_correct(c, solution)
            def if_wrong():
                self.ctx.stats.increment('captcha', tags={'cached': 'False', 'correct': 'False'})
                self.ctx.captcha_cache.report_incorrect(c, solution)
        return solution, if_right, if_wrong

    def try_fetch_and_store_document(self, code):
        self.ctx.stats.increment('fetch_document')
        self.logger.debug('fetching document code=%s', code)
        # TODO this control flow is a bit ugly
        try:
            start_time = time.time()
            result = self.fetch_document(code)
        except Exception as e: # TODO too general?
            self.ctx.stats.increment('fetched_document', tags={'result': 'ERROR'})
            self.logger.debug('document code=%s EXCEPTION %s', code, repr(e)) # so text=True means the document was empty. this is backwards, my (nspin) fault. but DO NOT CHANGE THIS, because our logs should be consistent. i am sorry :(
            self.ctx.document_store.put_error(code, repr(e))
            raise e
        else:
            running_time = time.time() - start_time
            self.ctx.stats.timing('fetch_document_duration', running_time * 1000)
            tag = '{}_{}'.format('OLD' if result.is_old else 'NEW', 'ABSENT' if result.text is None else 'PRESENT')
            self.ctx.stats.increment('fetched_document', tags={'result': tag})
            self.logger.debug('document code=%s OK %s', code, result._replace(text=result.text is None)) # so text=True means the document was empty. this is backwards, my (nspin) fault. but DO NOT CHANGE THIS, because our logs should be consistent. i am sorry :(
            self.ctx.document_store.put(code, result.text, result.is_old)

    def do_session(self):
        session_over = mk_has_passed(self.ctx.sched.session_length())
        while not session_over():
            self.try_fetch_and_store_document(self.ctx.document_store.next_code())

CONN_EX_LIMIT = 5

def _check(f, codes, *args, **kwargs):
    ex = None
    for _ in range(CONN_EX_LIMIT): # arbitrary
        try:
            resp = f(*args, **kwargs)
        except ConnectionError as e:
            ex = e
            # TODO what to do here?
            # raise ScraperConnectionException('_check failed on', f, args, kwargs, 'with', e)
            time.sleep(5)
        except RequestException as e:
            raise ScraperUnexpectedOtherException(e, '_check failed on', f, args, kwargs)
        else:
            if resp.status_code in codes:
                return resp
            msg = 'failed check_resp url={} code={} reason={}'.format(resp.url, resp.status_code, resp.reason)
            cons = ScraperBadTorExitException if resp.status_code == 403 else ScraperUnexpectedFlowException
            raise cons(msg)
    raise ScraperBadTorExitException('_check cause connection errors', CONN_EX_LIMIT, 'times', 'last one was', ex, 'called with', f, args, kwargs)


def is_document_captcha_page(text):
    return 'id="cphMain_pnlCaptcha"' in text

# TODO(nspin) Handle "new" empty documents.
def is_present_document_page(text):
    return 'id="cphMain_pnlShowNews"' in text

# TODO(nspin) Make more efficient.
# TODO(nspin) Handle "new" empty documents.
def is_absent_document_page(text):
    try:
        div, = BeautifulSoup(text, 'html.parser').find_all('div', class_='Padder10')
        l, subdiv, r = div.children
        class_, = subdiv['class']
        return l == '\n' and r == '\n' and class_ == 'Marginer7'
    except (ValueError, KeyError):
        return False

def extract_document_captcha_path(soup):
    return soup.find(id='imgCaptcha')['src'].lstrip('..')

def mk_document_captcha_form_data(soup, captcha_solution):
    data = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        'ctl00$cphMain$captcha$txtCaptcha': captcha_solution,
        }
    form = soup.find(id='form1')
    fields = [
        '__VIEWSTATE',
        '__VIEWSTATEGENERATOR',
        '__VIEWSTATEENCRYPTED',
        '__EVENTVALIDATION',
        'ctl00$cphMain$btnCaptcha',
        ]
    for field in fields:
        data[field] = form.find(attrs={'name': field})['value']
    return data
