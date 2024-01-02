"""
The httpproxy module exposes :py:class:`HttpProxy`, whose :py:meth:`httpproxy.rest_proxy` 
method handles each request.

By default the httpproxy module expects to support secure transmission protocols.
"""
import os
from http.client import responses

from diskcache import Cache
import mime
import urllib3
from urllib3 import ProxyManager, make_headers


class HttpProxy:
    """
    The http proxy

    By default this class does not persist anything.

    Enable persistence by setting the global configuration option `no_cache` = **False**

    :param config: The global Creepo config

    :param key: The storage key **AND** path prefix

    """

    def __init__(self, config, key):
        self.key = key
        self.config = config
        self._no_cache = True
        self.logger = config['logger']

        if config.get('no_cache') is not None:
            if f"{config.get('no_cache')}" == 'False':
                self._no_cache = False

        self.creepo = os.path.join(os.environ.get('HOME'), '.CREEPO_BASE')

        if os.environ.get('CREEPO_BASE') is not None:
            self.creepo = os.environ.get('CREEPO_BASE')

    @property
    def base(self):
        """The base path to storage"""
        return f"{self.creepo}/{self.key}"

    @property
    def kind(self):
        """The kind of proxy"""
        return self.key

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

    def gethttp(self):
        """convenience method to configure the http request engine"""
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
        return http

    def getheaders(self, environ):
        """convenience method to get the proper headers for the request"""
        headers = environ['headers']

        headers['content-type'] = self.mimetype(
            environ['path'], environ['content_type'])
        if self.config.get('credentials') is not None:
            headers = headers | urllib3.make_headers(
                basic_auth=self.config.get('credentials').get('username') + ':' +
                self.config.get('credentials').get('password')
            )
        return headers

    def dynamic_config(self, new_host):
        """convenience method to generate a new config for a dynamic proxy"""
        return {
            'no_cache': self.no_cache,
            'logger': self.config['logger'],
            f"{self.key}": {
                'registry': new_host,
            }
        }

    def rest_proxy(self, environ, start_response):
        """
        The rest_proxy method is the work engine for everything

        :param environ: The request Dictionary

        :param start_response: The CherryPy callback


        When environ contains a callback function that callback will be called 
        after the initial request.

        The callback might change the content.  For this reason we replace the 
        Content-Length header after the callback.

        The (potentially modified) response is returned to the caller as a 
        byte array at request['response']
        """
        environ['output_filename'] = environ['path']

        callback = environ.get('callback')

        if self.no_cache or Cache(self.base).get(environ['output_filename']) is None:
            http = self.gethttp()
            headers = self.getheaders(environ)

            source_url = f"{self.config[self.key]['registry']}{environ['path']}"

            splitpath = environ['output_filename'].split('/')

            if not source_url.endswith('/'):
                # Remove the filename
                splitpath.pop()

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
                self.logger.warning(
                    '%s.%s ***WARNING***: Unexpected status %d for %s',
                    self.kind, __name__, r.status, source_url)
                start_response(
                    f"{r.status} {responses[r.status]}", list(r.headers.items()))
                yield r.data
            r.release_conn()
            if not self.no_cache and environ.get('response') is not None:
                self.persist(environ)
        else:

            start_response('200 OK', [
                           ('Content-Type',
                            self.mimetype(environ['path'], environ['content_type']))])
            with Cache(self.base) as cache:
                result = cache.get(environ['output_filename'])
                yield result
