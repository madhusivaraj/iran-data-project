from scraper import *
import itertools
from threading import Thread, Lock
from queue import Queue
import time
import random

limiter = ConcurrencyLimiter(
    max_running = 5,
    )

lock = Lock()
running = 0
q = Queue()

def target(i):
    global running
    try:
        for j in itertools.count():
            with limiter.guard():
                with lock:
                    print('{}\t{}\tbegin'.format(i, j))
                    running += 1
                    print('running: ', running)
                time.sleep(random.randint(1000, 5000)/1000)
                with lock:
                    print('{}\t{}\tend'.format(i, j))
                    running -= 1
                    print('running: ', running)
    except Exception as e:
        q.put(e)

for i in range(100):
    Thread(target=target, daemon=True, args=(i,)).start()
raise q.get()
