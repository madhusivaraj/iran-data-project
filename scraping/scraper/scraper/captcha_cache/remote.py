from base64 import b64decode, b64encode
from binascii import hexlify
from urllib.parse import quote

import requests

URL_PREFIX = 'http://captcha-storage.herokuapp.com/captcha/'

def mk_url(c):
    return URL_PREFIX + hexlify(c).decode('ascii')

def debug_get(c):
    return requests.get(mk_url(c)).json()

def get(c):
    return None
    resp = requests.get(mk_url(c))
    solution = resp.json()['solution']
    if solution == '':
        return None
    else:
        return solution

def report_correct(c, solution):
    resp = requests.post(mk_url(c), json={
        'c_param': b64encode(c).decode('ascii'),
        'solution': solution,
        })
    resp.raise_for_status()

def report_incorrect(c, solution):
    resp = requests.get(mk_url(c))
    data = resp.json()
    data['c_param'] = b64encode(c).decode('ascii')
    if solution not in data['failed-attempts']:
        data['failed-attempts'].append(solution)
    if data['solution'] == solution:
        data['solution'] = ''
    resp = requests.post(mk_url(c), json=data)
    resp.raise_for_status()

def report_unexpected_incorrect(c, solution):
    report_incorrect(c, solution)
