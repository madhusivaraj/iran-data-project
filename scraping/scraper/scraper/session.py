import logging

import random

from requests import Session
from user_agent import generate_user_agent

from scraper.util import deobfuscate, nullcontext
from scraper.exceptions import *

TARGET_HOST = deobfuscate('jjj.eex.ve')
SEARCH_URL = 'http://' + TARGET_HOST + '/News/NewsList.aspx'

def is_old_url_for(code, url):
    return url == 'http://{}/News/ShowOldNews.aspx?Code={}'.format(TARGET_HOST, code)

class ScrapeSession(Session):
    '''
    Simple wrapper around a requests.Session for interacting with the target website.
    '''

    def __init__(self, proxy_url=None, rate_limit_ctx=None, timer_ctx=None):
        super().__init__()
        self.logger = logging.getLogger(__name__).getChild(repr(self))
        self.headers = _generate_headers()
        if proxy_url is not None:
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url,
            }
        self.rate_limit_ctx = nullcontext if rate_limit_ctx is None else rate_limit_ctx
        self.timer_ctx = nullcontext if timer_ctx is None else timer_ctx


    def get_captcha(self, path):
        with self.rate_limit_ctx():
            with self.timer_ctx():
                return self.get(mk_captcha_url(path), allow_redirects=False, headers=self.headers)

    def get_document(self, code, old=False):
        with self.rate_limit_ctx():
            with self.timer_ctx():
                return self.get(mk_document_url(code, old=old), allow_redirects=False, headers=self.headers)

    def post_document(self, code, data, old=False):
        with self.rate_limit_ctx():
            with self.timer_ctx():
                return self.post(mk_document_url(code, old=old), data=data, allow_redirects=False, headers=self.headers)

    # TODO how to handle issues with ipecho.net, how common are they?
    def external_ip(self):
        r = self.get('http://ipecho.net/plain')
        r.raise_for_status()
        return r.text


def mk_document_url(code, old=False):
    old_str = 'Old' if old else ''
    return 'http://{}/News/Show{}News.aspx?Code={}'.format(TARGET_HOST, old_str, code)

def mk_captcha_url(path):
    return 'http://' + TARGET_HOST + path

def _generate_headers():
    possible_extra_mime_types = ('application/xhtml+xml', 'application/xml;q=0.9', 'image/webp', 'image/apng', '*/*;q=0.8')
    accept = ','.join(('text/html',) + _at_least_1(possible_extra_mime_types))

    possible_encodings = ('gzip', 'deflate', 'br')
    accept_encodings = ','.join(_at_least_1(possible_encodings))

    return {
        'User-Agent': generate_user_agent(),
        'accept': accept,
        'accept-encoding': accept_encodings,
        'upgrade-insecure-requests': '1',
        'accept-language' : 'en-US,en;q=0.9'
        }

def _at_least_1(xs):
    return tuple(random.sample(xs, random.randint(1, len(xs))))
