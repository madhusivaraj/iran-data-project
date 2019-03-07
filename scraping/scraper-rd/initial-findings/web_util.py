import re
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from PIL import Image

from util import deobfuscate
from solve_captcha import solve_captcha

TARGET_DOMAIN = deobfuscate('jjj.eex.ve')

def mk_show_news_url(code):
    return deobfuscate('uggc://jjj.eex.ve/Arjf/FubjArjf.nfck?Pbqr=') + str(code)

captcha_re = re.compile(r'(?P<attr>../HttpHandler/Captcha.ashx\?w=(?P<w>[0-9]+)&h=(?P<h>[0-9]+)&c=(?P<c>[^&]+)&bc=(?P<bc>[0-9a-f]+)&rnd=(?P<rnd>[0-9]+))')

CAPTCHA_WIDTH = 400
CAPTCHA_HEIGHT = 200
CAPTCHA_BACKGROUND_COLOR = 'ffffff'
CAPTCHA_RND = 1337

def mk_captcha_url(c, w=CAPTCHA_WIDTH, h=CAPTCHA_HEIGHT, bc=CAPTCHA_BACKGROUND_COLOR, rnd=CAPTCHA_RND):
    return 'http://{}/HttpHandler/Captcha.ashx'.format(TARGET_DOMAIN) \
        + '?w={}&h={}&c={}&bc={}&rnd={}'.format(w, h, c, bc, rnd)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
    }

def is_captcha_page(text):
    return 'id="cphMain_pnlCaptcha"' in text

def is_news_page(text):
    return 'id="cphMain_pnlShowNews"' in text

# Returns form data
def solve_captcha_page(text):
    soup = BeautifulSoup(text, 'html.parser')

    src = soup.find(id='imgCaptcha')['src']
    m = captcha_re.search(src)
    if m is None:
        raise Exception('no captcha_re match: {}'.format(src))
    url = mk_captcha_url(m['c'], rnd=m['rnd'])

    # TODO(nspin) Is it suspicious to request so many captchas without a cookie?
    # TODO(nspin) Consider passing session through here.
    resp = requests.get(url)
    resp.raise_for_status()
    im = Image.open(BytesIO(resp.content))
    solution = solve_captcha(im)

    return mk_captcha_form_data(soup, solution)

def mk_captcha_form_data(soup, captcha_solution):
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
