"""
The httpproxy module exposes class `Proxy`, which is the base request endpoint.

By default the httpproxy module expects to support secure transmission protocols.
"""
import errno
import os
from http.client import responses
from diskcache import Cache
import mime
import urllib3
from urllib3 import ProxyManager, make_headers


class Proxy:
    """
    The http proxy

    By default this class does not persist anything.

    Enable persistence by setting the global configuration option `no_cache` = **False**
    """

    def __init__(self, _kind, config, global_config):
        self.cache = None
        self._kind = _kind
        self.config = config
        no_cache = True
        if global_config.get('no_cache') is not None:
            no_cache = global_config.get('no_cache') != 'False'
        self._no_cache = no_cache
        self._upstream = config['registry']
        self._upstream_url = urllib3.util.parse_url(config['registry'])
        self._creepo = os.path.join(os.environ.get('HOME'), '.CREEPO_BASE')

        if os.environ.get('CREEPO_BASE') is not None:
            self._creepo = os.environ.get('CREEPO_BASE')

    @property
    def base(self):
        """The base path to storage"""
        return self._creepo

    @property
    def kind(self):
        """The kind of proxy"""
        return self._kind

    @property
    def no_cache(self):
        """The no_cache property for this :class:`Proxy`"""
        return self._no_cache

    def mimetype(self, path, default):
        """Return the default mimetype for the proxy"""

        if len(mime.Types.of(path)) > 0:
            return mime.Types.of(path)[0].content_type
        return default

    def persist(self, request):
        """Persist the (possibly changed) data"""
        if not self.no_cache:
            with Cache(self.base) as cache:
                cache.set(request['output_filename'], request['response'])

    def proxy(self, request, callback, start_response, logger):
        """The proxy method is the work engine for everything, including caching, if enabled"""
        request['output_filename'] = f"{self._creepo}/{request['storage']}{request['path']}"
        status = 200
        response_headers = None
        content_type = self.mimetype(request['path'], request['content_type'])

        if Cache(self.base).get(request['output_filename']) is None:
            logger.debug('%s.%s Requesting [%s] from [%s]',
                         self._kind, __name__, request['path'], self._upstream_url)

            ca_certs = ()
            if self.config.get('cacert') is not None:
                ca_certs = self.config['cacert']

            logger.debug('%s.%s ca_certs is %s for %s', self._kind,
                         __name__, ca_certs, self._upstream_url)

            http = urllib3.PoolManager(ca_certs=ca_certs, num_pools=10000)

            if self.config.get('proxy') is not None:
                default_headers = make_headers()
                if self.config.get('proxy_user') is not None:
                    default_headers = make_headers(
                        proxy_basic_auth=self.config['proxy_user'] +
                        ':' + self.config['proxy_password'])
                http = ProxyManager(self.config.get(
                    'proxy'), proxy_headers=default_headers, num_pools=10000)

            headers = request['headers']
            headers['content-type'] = content_type
            if self.config.get('credentials') is not None:
                headers = headers | urllib3.make_headers(
                    basic_auth=self.config.get('credentials').get('username') + ':' +
                    self.config.get('credentials').get('password')
                )

            logger.debug('%s.%s HEADERS: %s', self._kind, __name__, headers)
            source_url = f"{self._upstream}{request['path']}"

            splitpath = request['output_filename'].split('/')
            if not source_url.endswith('/'):
                # Remove the filename
                splitpath.pop()
            file_path = '/'.join(splitpath)
            logger.info('%s.%s file_path is %s',
                        self._kind, __name__, file_path)
            if file_path:
                if not os.path.exists(file_path) and self.no_cache is False:
                    logger.debug('%s.%s Creating folder(s) %s',
                                 self._kind, __name__, file_path)
                    try:
                        os.makedirs(file_path)
                    except OSError as e:
                        if e.errno != errno.EEXIST:
                            raise
                logger.debug('%s.%s %s %s', self._kind, __name__,
                             request['method'], request['path'])
                if request['path'].endswith('/'):
                    request['output_filename'] = request['output_filename'] + '.index'
                with http.request(
                    'GET',
                    source_url,
                    decode_content=False,
                    preload_content=False,
                    headers=headers,
                ) as r:
                    status = r.status

                    logger.debug("%s.%s STATUS: %d %s", self._kind,
                                 __name__, r.status, source_url)
                    logger.debug('%s.%s RESPONSE HEADERS: %s',
                                 self._kind, __name__, r.headers)
                    if r.status < 400:
                        if callback is not None:
                            # The callback must set request['response']
                            callback(r.data, request)

                            r.headers.discard('Content-Length')
                            response_headers = list(r.headers.items())
                            start_response(
                                f"{r.status} {responses[r.status]}",
                                response_headers)(request['response'])
                        else:
                            start_response(
                                f"{r.status} {responses[r.status]}", list(r.headers.items()))
                            yield r.data
                            request['response'] = r.data
                    else:
                        logger.warning(
                            '%s.%s ***WARNING***: Unexpected status %d for %s',
                            self._kind, __name__, r.status, source_url)
                        start_response(
                            f"{r.status} {responses[r.status]}", list(r.headers.items()))
                        yield r.data

                    r.release_conn()
                    if not self.no_cache and request['response'] is not None:
                        self.persist(request)
            else:
                logger.warning(
                    '%s.%s WARNING: There is no file_path for %s', self._kind, __name__, source_url)
        else:
            if response_headers is None:
                response_headers = [('Content-Type',  content_type)]

            logger.debug('%s.%s %s is cached', self._kind,
                         __name__, request['output_filename'])
            start_response(f"{status} {responses[status]}", response_headers)
            with Cache(self.base) as cache:
                yield cache.get(request['output_filename'])
