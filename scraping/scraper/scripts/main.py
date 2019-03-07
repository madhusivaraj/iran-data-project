import os
import os.path
import sys
import logging
from argparse import ArgumentParser

import boto3
import datadog

from scraper import *

DATADOG_API_KEY = os.environ['DATADOG_API_KEY']
DATADOG_APP_KEY = os.environ['DATADOG_APP_KEY']
AWS_ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
AWS_SECRET_KEY = os.environ['AWS_SECRET_KEY']

parser = ArgumentParser()
parser.add_argument('--nthreads', type=int, default=10)
parser.add_argument('--start-index', type=int, default=0)
parser.add_argument('--code-range', type=int, nargs=2, default=(12000000, 14000000))
parser.add_argument('--requests-per-second', type=float, default=1)
parser.add_argument('--log-dir', default='logs', help='requests per second')
args = parser.parse_args()

os.makedirs(args.log_dir, exist_ok=True)

# Logging
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger('datadog').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('nose').setLevel(logging.WARNING)
logging.basicConfig(
    format="%(asctime)s %(name)-5.5s [%(threadName)-4.4s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(args.log_dir, 'scraper.log')),
        logging.StreamHandler(sys.stderr),
    ])

logger = logging.getLogger(__name__)
logger.debug('args: %s', args)

# Configuration
nthreads = args.nthreads
ntesseract_processes = 10
socks_host = 'localhost'
socks_port = 9050
start_index = args.start_index
code_range = args.code_range
requests_per_second = args.requests_per_second
s3_bucket_name = "iran-article-html"

# DataDog
datadog.initialize(
    api_key=DATADOG_API_KEY,
    app_key=DATADOG_APP_KEY,
    )
stats = datadog.ThreadStats()
stats.start()
wrapped_stats = WrappedStats(stats)

mk_proxy_url = 'socks5h://u{{}}:p{{}}@{}:{}'.format(socks_host, socks_port).format

global_ctx = GlobalContext(
    mk_proxy_url = mk_proxy_url,
    rate_limiter = RateLimiter(requests_per_second),
    # tesseract_guard = ConcurrencyLimiter(max_running=ntesseract_processes).guard,
    )

code_tracker = CodeTracker(start_index, code_range)

def mk_thread_ctx():
    return ThreadContext(
        # sched = RandomScheduler(speed=5), # TODO too slow?
        sched = LameScheduler(),
        stats = wrapped_stats,
        captcha_cache = remote_captcha_cache,
        document_store = S3DocumentStore(
            code_tracker,
            boto3.Session(
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
                ),
            bucket_name=s3_bucket_name,
            ),
        )

scrape(nthreads, global_ctx, mk_thread_ctx)
