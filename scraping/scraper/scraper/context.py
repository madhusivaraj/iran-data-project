'''
Notes on mk_proxy_url:

    [type]
        (thread, iteration) -> proxy url or None

    [purpose]
        A proxy url of the form socks5h://<username>:<password>@host:port causes
        the HTTP client to use Tor via a SOCKS5 proxy.

        The socks5h: prefix (as opposed to just socks5:) ensures that DNS
        resolution happens through tor.

        The Tor SOCKS5 proxy doesn’t actually authenticate clients. Instead, it has
        a feature called IsolateSocksAuth, which causes Tor to isolate streams that
        authenticate to the SOCKS5 proxy using a different username and password.
        That is, streams that authenticate with different credentials will not share
        circuits through the Tor network.

    [example]
        mk_proxy_url = 'socks5h://u{{}}:p{{}}@{}:{}'.format(socks_host, socks_port).format
'''

from collections import namedtuple

ThreadContext = namedtuple('ThreadContext', [
    'sched',
    'captcha_cache',
    'document_store',
    'stats',
    ])

GlobalContext = namedtuple('GlobalContext', [
    'mk_proxy_url', # (thread, iteration) -> proxy url or None
    'rate_limiter',
    ])
