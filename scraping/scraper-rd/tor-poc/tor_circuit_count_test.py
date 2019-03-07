import os
import time
import itertools
from queue import Queue
from threading import Thread
from collections import namedtuple
from argparse import ArgumentParser

import requests
from stem import Signal
from stem.control import Controller

IP_ECHO_URL = 'http://ipecho.nickspinale.com'

MESSAGE_TYPE_NEW_EXIT = 0
MESSAGE_TYPE_NCIRCUITS = 1
MESSAGE_TYPE_EXCEPTION = 2
MESSAGE_TYPE_ERROR = 3

DT_OK_REUSE = 600
MONITOR_GRANULARITY = 5

Message = namedtuple('Message', 'time thread type body')

def worker(thread, q, socks_port, dt):
    def put_msg(ty, body):
        q.put(Message(time.time(), thread, ty, body))

    prev_exit_ip_addr = None
    for i in itertools.count(0):
        proxy = 'socks5h://thread-{}:iteration-{}@localhost:{}'.format(thread, i, socks_port)
        proxies = {
            'http': proxy,
            'https': proxy,
            }
        t = time.time() + dt
        curr_exit_ip_addr = None
        while time.time() < t:
            try:
                resp = requests.get(IP_ECHO_URL, proxies=proxies)
                resp.raise_for_status()
            except Exception as e:
                put_msg(MESSAGE_TYPE_EXCEPTION, e)
            else:
                exit_ip_addr = resp.text.strip()
                if curr_exit_ip_addr is None:
                    put_msg(MESSAGE_TYPE_NEW_EXIT, exit_ip_addr)
                    curr_exit_ip_addr = exit_ip_addr
                    if curr_exit_ip_addr == prev_exit_ip_addr:
                        put_msg(MESSAGE_TYPE_ERROR, 'prev and curr exit ip addr do not differ')
                        return
                elif exit_ip_addr != curr_exit_ip_addr:
                    # put_msg(MESSAGE_TYPE_ERROR, 'exit ip addr changed unexpectedly from {} to {}'.format(curr_exit_ip_addr, exit_ip_addr))
                    # return
                    curr_exit_ip_addr = exit_ip_addr
        prev_exit_ip_addr = curr_exit_ip_addr

def circuit_monitor(q, control_port):
    def put_msg(ty, body):
        q.put(Message(time.time(), 'monitor', ty, body))

    try:
        with Controller.from_port(port=control_port) as ctrl:
            ctrl.authenticate()
            ncircuits = None
            while True:
                circuits = ctrl.get_circuits()
                if ncircuits is None or len(circuits) != ncircuits:
                    ncircuits = len(circuits)
                    put_msg(MESSAGE_TYPE_NCIRCUITS, ncircuits)
                time.sleep(MONITOR_GRANULARITY)

    except Exception as e:
        put_msg(MESSAGE_TYPE_ERROR, repr(e))

def run(nthreads, dt, socks_port, control_port):
    q = Queue()

    def stagger():
        for i in range(nthreads):
            Thread(target=worker, name='worker', daemon=True, args=(i, q, socks_port, dt)).start()
            time.sleep(dt / nthreads)

    Thread(target=stagger, name='stagger', daemon=True).start()
    Thread(target=circuit_monitor, name='circuit_monitor', daemon=True, args=(q, control_port)).start()

    t0 = time.time()
    used_exits = {}

    while True:
        msg = q.get()
        if msg.type == MESSAGE_TYPE_NEW_EXIT:
            print('{:12.6f}s {:3}t NEW EXIT {}'.format(msg.time - t0, msg.thread, msg.body))
            now = time.time()
            if msg.body in used_exits:
                dt_reuse = now - used_exits[msg.body]
                print('*EXIT REUSE: {} after {}s*'.format(msg.body, dt_reuse))
                # assert dt_reuse > DT_OK_REUSE
            used_exits[msg.body] = now
        elif msg.type == MESSAGE_TYPE_NCIRCUITS:
            print('N={}'.format(msg.body))
        elif msg.type == MESSAGE_TYPE_EXCEPTION:
            print('{:12.6f}s <{:3}> EXCEPTION {}'.format(msg.time - t0, msg.thread, msg.body))
        else:
            assert msg.type == MESSAGE_TYPE_ERROR
            print('*UH OH {}*'.format(msg))
            # print('*ERROR*')
            # print(msg)
            # return

def main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--socks-port', type=int, default=9050)
    parser.add_argument('-c', '--control-port', type=int, default=9051)
    parser.add_argument('nthreads', type=int)
    parser.add_argument('dt', type=float)
    args = parser.parse_args()
    run(args.nthreads, args.dt, args.socks_port, args.control_port)

if __name__ == '__main__':
    main()
