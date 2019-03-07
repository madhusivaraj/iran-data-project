import time
import logging
import itertools
from queue import Queue
from threading import Thread

from requests import RequestException

from scraper.worker import Worker
from scraper.session import ScrapeSession
from scraper.exceptions import *


def scrape_target(thread, global_ctx, thread_ctx):
    logger = logging.getLogger(__name__).getChild('t{}'.format(thread)) # different logger for each worker
    
    time.sleep(thread_ctx.sched.initial_delay())

    for i in itertools.count(0):

        proxy_url = global_ctx.mk_proxy_url(thread, i)
        logger.debug('session %s: starting with proxy_url=%s', i, proxy_url)
        sess = ScrapeSession(
            proxy_url=proxy_url,
            rate_limit_ctx=global_ctx.rate_limiter.guard,
            timer_ctx=lambda: thread_ctx.stats.timer('response_latency'),
            )

        try:
            ext_ip = sess.external_ip()
        except RequestException as e:
            logger.warn('session %s: sess.external_ip() raised %s', i, repr(e))
            ext_ip = 'unknown'
        else:
            logger.debug('session %s: exit ip is %s', i, ext_ip)

        try:
            Worker(sess, global_ctx, thread_ctx).do_session()
        except ScraperBadTorExitException as e:
            logger.warn('session %s: exit ip %s is is probably bad: raised %s', i, ext_ip, e)
            pass # DO MORE STUFF HERE
        except ScraperUnexpectedFlowException as e:
            logger.error('session %s: exit ip %s: unexpected flow: %s', i, ext_ip, e)
        except ScraperUnexpectedOtherException as e:
            logger.error('session %s: exit ip %s: unexpected exception: %s\n%s', i, ext_ip, e, e.show())

        time.sleep(thread_ctx.sched.session_delay())


# TODO provide means of terminating child threads
def scrape(nthreads, global_ctx, mk_thread_ctx):
    q = Queue()
    for i in range(nthreads):
        def target(i_):
            try:
                scrape_target(i_, global_ctx, mk_thread_ctx())
            except Exception as e:
                q.put(e)
        Thread(target=target, name='t{}'.format(i), daemon=True, args=(i,)).start()
    raise q.get()
