from requests import Session

from web_util import *
from requests import Session

A = mk_show_news_url('14065595')
B = mk_show_news_url('14066178')
C = mk_show_news_url('14076240')

def normal_flow():
    sess = Session()

    r1 = sess.get(A)
    r1.raise_for_status()
    assert is_captcha_page(r1.text)

    data = solve_captcha_page(r1.text)

    r2 = sess.post(A, headers=HEADERS, data=data)
    r2.raise_for_status()
    assert is_news_page(r2.text)

    return r2.text

# :(
def discontinuous():
    r1 = Session().get(A)
    r1.raise_for_status()
    assert is_captcha_page(r1.text)

    data = solve_captcha_page(r1.text)

    r2 = Session().post(A, headers=HEADERS, data=data)
    r2.raise_for_status()
    assert is_news_page(r2.text)

    return r2.text

# :)
def change_code():
    sess = Session()

    a = sess.get(A)
    a.raise_for_status()
    assert is_captcha_page(a.text)

    data = solve_captcha_page(a.text)

    b = sess.post(B, headers=HEADERS, data=data)
    b.raise_for_status()
    assert is_news_page(b.text)

    return b.text

# :(
def reuse_form():
    sess = Session()

    a1 = sess.get(A)
    a1.raise_for_status()
    assert is_captcha_page(a1.text)

    data = solve_captcha_page(a1.text)

    a2 = sess.post(B, headers=HEADERS, data=data)
    a2.raise_for_status()
    assert is_news_page(a2.text)

    b = sess.post(B, headers=HEADERS, data=data)
    b.raise_for_status()
    assert is_news_page(b.text)

    return a2, b
