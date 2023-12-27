"""The httpproxy"""
import errno
import os
from http.client import responses

import mime
import urllib3
from urllib3 import ProxyManager, make_headers


class Proxy:  # pylint: disable=too-few-public-methods
    """
    The http proxy

    By default this class does not persist anything.

    Enable persistence by setting the global configuration option no_cache = False
    """

    def __init__(self, _type, config, global_config):
        self._type = _type
        self.config = config
        self.no_cache = True
        if global_config.get('no_cache') is not None:
            self.no_cache = global_config.get('no_cache') == 'True'

        self._upstream = config['registry']
        self._upstream_url = urllib3.util.parse_url(config['registry'])
        self._creepo = os.path.join(os.environ.get('HOME'), '.CREEPO_BASE')

        if os.environ.get('CREEPO_BASE') is not None:
            self._creepo = os.environ.get('CREEPO_BASE')
        if not os.path.exists(self._creepo) and self.no_cache is False:
            os.makedirs(self._creepo)

    @property
    def base(self):
        """The base path to storage"""
        return self._creepo

    @property
    def type(self):
        """The type of proxy"""
        return self._type

    def mimetype(self, path, default):
        """Return the default mimetype for the proxy"""

        if len(mime.Types.of(path)) > 0:
            return mime.Types.of(path)[0].content_type
        return default

    def persist(self, _input, request, logger):
        """Persist the (possibly changed) data"""
        if not self.no_cache:
            with open(request['output_filename'], 'wb') as outfile:
                try:
                    outfile.write(_input)
                    logger.debug('%s.%s Wrote %d byte() to %s', self._type,
                                 __name__, len(_input), request['output_filename'])
                except TypeError as e:
                    logger.warning(
                        '%s.%s Caught exception %s while trying to write %d bytes to %s',
                        self._type, __name__, e, len(
                            _input), request['output_filename'])
                outfile.close()
        request['response'] = _input

    def proxy(self, request, callback, start_response, logger):
        """The proxy method"""
        request['output_filename'] = f"{self._creepo}/{request['storage']}{request['path']}"
        status = 200
        response_headers = None
        content_type = self.mimetype(request['path'], request['content_type'])
        if not os.path.exists(request['output_filename']):
            logger.debug('%s.%s Requesting [%s] from [%s]',
                         self._type, __name__, request['path'], self._upstream_url)

            ca_certs = ()
            if self.config.get('cacert') is not None:
                ca_certs = self.config['cacert']

            logger.debug('%s.%s ca_certs is %s for %s', self._type,
                         __name__, ca_certs, self._upstream_url)

            http = urllib3.PoolManager(ca_certs=ca_certs, num_pools=10)

            if self.config.get('proxy') is not None:
                default_headers = make_headers()
                if self.config.get('proxy_user') is not None:
                    default_headers = make_headers(
                        proxy_basic_auth=self.config['proxy_user'] +
                        ':' + self.config['proxy_password'])
                http = ProxyManager(self.config.get(
                    'proxy'), proxy_headers=default_headers)

            headers = request['headers']
            headers['content-type'] = content_type
            if self.config.get('credentials') is not None:
                headers = headers | urllib3.make_headers(
                    basic_auth=self.config.get('credentials').get('username') + ':' +
                    self.config.get('credentials').get('password')
                )

            logger.debug('%s.%s HEADERS: %s', self._type, __name__, headers)
            source_url = f"{self._upstream}{request['path']}"

            splitpath = request['output_filename'].split('/')
            if not source_url.endswith('/'):
                # Remove the filename
                splitpath.pop()
            file_path = '/'.join(splitpath)
            logger.info('%s.%s file_path is %s',
                        self._type, __name__, file_path)
            if file_path:
                if not os.path.exists(file_path) and self.no_cache is False:
                    logger.debug('%s.%s Creating folder(s) %s',
                                 self._type, __name__, file_path)
                    try:
                        os.makedirs(file_path)
                    except OSError as e:
                        if e.errno != errno.EEXIST:
                            raise
                logger.debug('%s.%s %s %s', self._type, __name__,
                             request['method'], request['path'])
                if request['path'].endswith('/'):
                    request['output_filename'] = request['output_filename'] + '.index'
                with http.request(
                    'GET',
                    source_url,
                    preload_content=False,
                    headers=headers,
                ) as r:
                    status = r.status

                    logger.debug("%s.%s STATUS: %d %s", self._type,
                                 __name__, r.status, source_url)
                    logger.debug('%s.%s RESPONSE HEADERS: %s',
                                 self._type, __name__, r.headers)
                    if r.status < 400:
                        # The callback must set request['response']
                        callback(r.data, request)
                    else:
                        logger.warning(
                            '%s.%s ***WARNING***: Unexpected status %d for %s',
                            self._type, __name__, r.status, source_url)
                        request['response'] = r.data

                    if r.headers.get('Content-Length') is not None:
                        if r.headers.get('Content-Length') != str(len(request['response'])):
                            logger.debug('%s.%s Remove Content-Length %s', self.type,
                                         __name__, r.headers.get('Content-Length'))
                            r.headers.discard('Content-Length')
                            logger.debug(
                                '%s.%s Add Content-Length %d',
                                self.type,
                                __name__,
                                len(request['response']))

                    response_headers = list(r.headers.items())

                    r.release_conn()
            else:
                logger.warning(
                    '%s.%s WARNING: There is no file_path for %s', self._type, __name__, source_url)
        else:
            logger.info('%s.%s File is cached: %s',
                        self._type, __name__, request['output_filename'])

        # if response_headers is None:

        if request['output_filename'].endswith('/'):
            request['output_filename'] = request['output_filename'] + '.index'

        if os.path.exists(request['output_filename']):
            with open(request['output_filename'], 'rb') as infile:
                content = infile.read()
                infile.close()
            if response_headers is None:
                response_headers = [('Content-Type',  content_type)]

            logger.debug('%s.%s %s is cached', self._type,
                         __name__, request['output_filename'])
            start_response(f"{status} {responses[status]}", response_headers)
            yield content
        else:
            if response_headers is None:
                response_headers = [('Content-Type',  'text/html')]

            if request.get('response') is not None:
                start_response(
                    f"{status} {responses[status]}", response_headers)
                yield request['response']
            else:
                status = 404
                logger.debug('%s.%s Not found %s', self._type,
                             __name__, request['output_filename'])
                start_response(
                    f"{status} {responses[status]}", response_headers)
                yield []
