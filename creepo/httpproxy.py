"""
The httpproxy module exposes class `Proxy`, which is the base request endpoint.

By default the httpproxy module expects to support secure transmission protocols.
"""
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
        self._no_cache = True

        if global_config.get('no_cache') is not None:
            if f"{global_config.get('no_cache')}" == 'False':
                self._no_cache = False

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

    def proxy(self, environ, start_response):
        """The proxy method is the work engine for everything, including caching, if enabled"""
        environ['output_filename'] = f"{environ['storage']}{environ['path']}"

        callback = environ.get('callback')

        if self.no_cache or Cache(self.base).get(environ['output_filename']) is None:

            ca_certs = ()
            if self.config.get('cacert') is not None:
                ca_certs = self.config['cacert']

            http = urllib3.PoolManager(ca_certs=ca_certs, num_pools=10000)

            if self.config.get('proxy') is not None:
                default_headers = make_headers()
                if self.config.get('proxy_user') is not None:
                    default_headers = make_headers(
                        proxy_basic_auth=self.config['proxy_user'] +
                        ':' + self.config['proxy_password'])
                http = ProxyManager(self.config.get(
                    'proxy'), proxy_headers=default_headers, num_pools=10000)

            headers = environ['headers']
            headers['content-type'] = self.mimetype(
                environ['path'], environ['content_type'])
            if self.config.get('credentials') is not None:
                headers = headers | urllib3.make_headers(
                    basic_auth=self.config.get('credentials').get('username') + ':' +
                    self.config.get('credentials').get('password')
                )

            source_url = f"{self._upstream}{environ['path']}"

            splitpath = environ['output_filename'].split('/')
            if not source_url.endswith('/'):
                # Remove the filename
                splitpath.pop()
            file_path = '/'.join(splitpath)

            if file_path:
                if environ['path'].endswith('/'):
                    environ['output_filename'] = environ['output_filename'] + '.index'
                r = http.request(
                    method='GET',
                    url=source_url,
                    decode_content=False,
                    preload_content=False,
                    headers=headers,
                )

                if r.status < 400:
                    if callback is not None:
                        # The callback must set request['response']
                        callback(r.data, environ)

                        r.headers.discard('Content-Length')

                        start_response(
                            f"{r.status} {responses[r.status]}",
                            list(r.headers.items()))
                        yield environ['response']
                    else:
                        start_response(
                            f"{r.status} {responses[r.status]}", list(r.headers.items()))
                        yield r.data
                        environ['response'] = r.data
                else:
                    environ['logger'].warning(
                        '%s.%s ***WARNING***: Unexpected status %d for %s',
                        self._kind, __name__, r.status, source_url)
                    start_response(
                        f"{r.status} {responses[r.status]}", list(r.headers.items()))
                    yield r.data
                r.release_conn()
                if not self.no_cache and environ.get('response') is not None:
                    self.persist(environ)
            else:
                environ['logger'].warning(
                    '%s.%s WARNING: There is no file_path for %s', self._kind, __name__, source_url)
        else:

            start_response('200 OK', [
                           ('Content-Type',
                            self.mimetype(environ['path'], environ['content_type']))])
            with Cache(self.base) as cache:
                result = cache.get(environ['output_filename'])
                yield result
