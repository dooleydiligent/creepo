"""

A composer proxy

"""
import io
import json
import urllib.parse
from urllib.parse import urlparse

import mime

import cherrypy

from proxy import Proxy


class ComposerProxy:
    """

    A composer proxy

    """

    def __init__(self, config, logger):
        self.logger = logger
        self.config = config
        self.key = 'p2'
        if self.key not in self.config:
            self.config[self.key] = {
                'registry': 'https://packagist.org', 'self': 'https://localhost:4443/p2'}

        self.proxy = Proxy(__name__, self.config[self.key])
        self.logger.debug('ComposerProxy instantiated with %s',
                          self.config[self.key])

    def noopcallback(self, _input_bytes, _outpath):
        """

        noopcallback

        """
        self.logger.debug('%s noopcallback for %s', __name__, _outpath)
        self.proxy.persist(_input_bytes, _outpath, self.logger)

    def callback(self, _input_bytes, _outpath):
        """

        callback - replace source and dist urls with self-relative urls

        """

        data = json.load(io.BytesIO(_input_bytes))

        for package in data['packages']:
            self.logger.debug('%s package is %s', __name__, package)
            for version in data['packages'][package]:
                if version.get('source') is not None:
                    version['source']['url'] = self.config[self.key]['self'] + \
                        '/source?q=' + \
                        urllib.parse.quote_plus(version['source']['url'])
                if version.get('dist') is not None:
                    version['dist'][
                        'url'] = self.config[self.key]['self'] + \
                        '/dist?q=' + \
                        urllib.parse.quote_plus(version['dist']['url'])

        content = json.dumps(data)
        self.proxy.persist(bytes(content, encoding="utf-8"),
                           _outpath, self.logger)

    @cherrypy.expose
    def p2(self, environ, start_response):
        """Proxy a composer request."""
        path = environ["REQUEST_URI"]
        if path == '/p2/packages.json':
            path = environ["REQUEST_URI"].removeprefix("/p2")

        self.logger.debug('%s %s composer(%s)', __name__,
                          cherrypy.request.method, path)

        newpath = path
        if cherrypy.request.query_string != '':
            self.logger.debug('%s QUERY_STRING: %s', __name__,
                              cherrypy.request.query_string)

        newrequest = {}
        newrequest['method'] = cherrypy.request.method
        newrequest['headers'] = {}
        newrequest['actual_request'] = cherrypy.request

        if len(newpath.split('?q=')) > 1:
            new_remote = urlparse(
                urllib.parse.unquote_plus(newpath.split('?q=')[1]))
            # Remove the leading / from the remaining path to get the storage bucket
            newrequest['storage'] = f"{newpath.split('?q=')[0][1:]}"
            newpath = new_remote.path
            if '?' not in newpath and '&' in newpath:
                newrequest['path'] = newpath.replace('&', '?', 1)
            else:
                newrequest['path'] = newpath

            if len(mime.Types.of(newpath.split('?')[0])) > 0:
                newrequest['content_type'] = mime.Types.of(newpath.split('?')[0])[
                    0].content_type
            else:
                newrequest['content_type'] = 'text/html'

            newhost = f"{new_remote.scheme}://{new_remote.netloc}"
            self.logger.info(
                '%s Create new proxy with host %s and path %s', __name__, newhost, new_remote.path)

            dynamic_proxy = Proxy(__name__, {'registry': newhost})
            return dynamic_proxy.proxy(newrequest, self.noopcallback, start_response, self.logger)

        if len(mime.Types.of(path)) > 0:
            newrequest['content_type'] = mime.Types.of(path)[
                0].content_type
        else:
            newrequest['content_type'] = 'application/octet-stream'

        newrequest['path'] = newpath
        newrequest['storage'] = self.key

        return self.proxy.proxy(newrequest, self.callback, start_response, self.logger)
