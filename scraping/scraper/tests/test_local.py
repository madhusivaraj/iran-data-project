import sys
import logging
import traceback

import boto3
import datadog

from scraper import *

import scraper_secrets

# Logging
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger('datadog').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('nose').setLevel(logging.WARNING)
logging.basicConfig(
    format="%(asctime)s [%(threadName)-2.2s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler(sys.stderr),
    ])

# DataDog
datadog.initialize(
    api_key=scraper_secrets.DATADOG_API_KEY,
    app_key=scraper_secrets.DATADOG_APP_KEY,
    )
stats = datadog.ThreadStats()
stats.start()
wrapped_stats = WrappedStats(stats)

# Scraper configuration
nthreads = 10
socks_host = 'localhost'
socks_port = 9050
start_index = 0
code_range = (12000000, 12000019)

mk_proxy_url = 'socks5h://u{{}}:p{{}}@{}:{}'.format(socks_host, socks_port).format
# mk_proxy_url = lambda *_: None # no tor

global_ctx = GlobalContext(
    mk_proxy_url = mk_proxy_url,
    rate_limiter = RateLimiter(1.0),
    )

def mk_ctx():
    return ThreadContext(

        # sched = RandomScheduler(), # tries to make sessions look real. use with more threads
        # stats=wrapped_stats, # calls are threadsafe
        # captcha_cache = remote_captcha_cache,
        # document_store=S3DocumentStore(
        #     CodeTracker(start_index, code_range),
        #     boto3.Session(
        #         aws_access_key_id=scraper_secrets.AWS_ACCESS_KEY,
        #         aws_secret_access_key=scraper_secrets.AWS_SECRET_KEY,
        #         ),
        #     bucket_name="iran-article-html-test",
        #     ),

        sched = LameScheduler(), # no waiting, except for rate limiting
        stats = NOPStats(), # calls don't do anything
        captcha_cache = LocalCaptchaCache(
            'local-storage/captchas.sqlite',
            'local-storage/captchas',
            ),
        document_store=LocalDocumentStore(
            'local-storage/documents.sqlite',
            'local-storage/documents',
            code_range,
            ),

        )

# Run with ability to inspect exception afterwards

ex = None
try:
    scrape(nthreads, global_ctx, mk_ctx)
except Exception as e:
    ex = e
traceback.print_tb(ex.__traceback__)
print(repr(ex))
print(dir(ex))
