import os
import time
from queue import Queue
from threading import Thread
from argparse import ArgumentParser

import requests
from stem import Signal
from stem.control import Controller

IP_ECHO_URL = 'http://ipecho.nickspinale.com'

MESSAGE_STATUS = 0
MESSAGE_EXCEPTION = 1
MESSAGE_CHANGED = 2
MESSAGE_LOG = 3

STATUS_GOOD = 0
STATUS_BAD = 1

def mastermind(control_port, q, min_time_with_nym):
    try:
        with Controller.from_port(port=control_port) as ctrl:
            ctrl.authenticate()
            while True:
                t = time.time()
                while not ctrl.is_newnym_available():
                    newnym_wait = ctrl.get_newnym_wait()
                    q.put((MESSAGE_LOG, (time.time(), 'must wait {:.4} sec for newnym'.format(newnym_wait))))
                    time.sleep(newnym_wait)
                q.put((MESSAGE_LOG, (time.time(), 'newnym available')))
                extra_wait = min_time_with_nym - (time.time() - t)
                if extra_wait > 0:
                    q.put((MESSAGE_LOG, (time.time(), 'waiting an extra {:.4} sec'.format(extra_wait))))
                    time.sleep(extra_wait)
                ctrl.signal(Signal.NEWNYM)
                q.put((MESSAGE_LOG, (time.time(), 'requested newnym')))
                q.put((MESSAGE_CHANGED, None))
    except Exception as e:
        q.put((MESSAGE_EXCEPTION, ('mastermind', e)))

def masked(identity, q, socks_port):
    proxy = 'socks5h://id{}:hunter2@localhost:{}'.format(identity, socks_port) # password doesn't matter
    proxies = {
        'http': proxy,
        'https': proxy,
        }
    while True:
        try:
            resp = requests.get(IP_ECHO_URL, proxies=proxies)
            resp.raise_for_status()
        except Exception as e:
            ok, val = (False, str(e))
        else:
            ip_addr = resp.text.strip()
            ok, val = (True, ip_addr)
        q.put((MESSAGE_STATUS, (identity, time.time(), ok, val)))

def monitor(num_identities, q):
    t0 = time.time()

    num_changes = 0
    statuses = []
    for i in range(num_identities):
        statuses.append((t0, False, ''))
    log = []

    term_rows, term_cols = map(int, os.popen('stty size', 'r').read().split())
    log_limit = term_rows - (8 + num_identities) - 2

    while True:

        os.system('clear')

        print('identity changes: {}'.format(num_changes))
        print('now:              {:.4f}'.format(time.time() - t0))
        print('')
        print(' identity  | last updated | ip addres or exception')
        print('-----------+--------------+-----------------------')
        for i, (t, ok, val) in enumerate(statuses):
            print('{:10} | {:12.6f} | {:60}'.format(i, t - t0, val))
        print('')
        print('log')
        print('---')
        for (t, msg) in log:
            print('{:12.4f}: {}'.format(t - t0, msg))

        msg_type, msg_val = q.get()
        if msg_type == MESSAGE_CHANGED:
            num_changes += 1
        elif msg_type == MESSAGE_STATUS:
            identity, t, ok, val = msg_val
            statuses[identity] = (t, ok, val)
        elif msg_type == MESSAGE_LOG:
            log.append(msg_val)
            if len(log) > log_limit:
                log.pop(0)
        else:
            assert msg_type == MESSAGE_EXCEPTION
            src, e = msg_val
            print(src)
            raise e

def go(num_identities, min_time_with_nym, socks_port, control_port):
    q = Queue()
    Thread(target=mastermind, name='mastermind', daemon=True, args=(control_port, q, min_time_with_nym)).start()
    for i in range(num_identities):
        Thread(target=masked, name='masked', daemon=True, args=(i, q, socks_port)).start()
    monitor(num_identities, q)

def main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--socks-port', type=int, default=9050)
    parser.add_argument('-c', '--control-port', type=int, default=9051)
    parser.add_argument('num_identities', type=int)
    parser.add_argument('min_time_with_nym', type=float)
    args = parser.parse_args()
    go(args.num_identities, args.min_time_with_nym, args.socks_port, args.control_port)

if __name__ == '__main__':
    main()
