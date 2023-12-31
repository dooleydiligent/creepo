"""
Alpine - proxy https://dl-cdn.alpinelinux.org/alpine/ to proxy apk packages
"""
import cherrypy

from httpproxy import Proxy


class ApkProxy:  # pylint: disable=too-few-public-methods
    """An apk proxy to help speed up docker builds"""

    def __init__(self, config):
        self.logger = config['logger']
        self.config = config
        self.key = 'alpine'
        if self.key not in self.config:
            self.config[self.key] = {
                'registry': 'https://dl-cdn.alpinelinux.org/alpine/'}

        self._proxy = Proxy(__name__, self.config[self.key], self.config)
        self.logger.debug('ApkProxy instantiated with %s',
                          self.config[self.key])

    @cherrypy.expose
    def proxy(self, environ, start_response):
        """Proxy an apk request."""
        path = environ["REQUEST_URI"].removeprefix("/alpine")
        self.logger.debug('%s %s proxy(%s)', __name__,
                          cherrypy.request.method, path)

        newpath = path

        newrequest = {}

        newrequest['content_type'] = self._proxy.mimetype(
            path, 'application/octet-stream')
        newrequest['method'] = cherrypy.request.method
        newrequest['path'] = newpath
        newrequest['headers'] = cherrypy.request.headers
        newrequest['storage'] = 'alpine'
        newrequest['actual_request'] = cherrypy.request
        newrequest['logger'] = self.logger

        return self._proxy.proxy(newrequest, start_response)
