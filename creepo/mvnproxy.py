"""
Apache maven - proxy https://repo.maven.apache.org/maven2 for use by java, 
scala, gradle, and similar tools
"""
import cherrypy

from httpproxy import Proxy


class MavenProxy:  # pylint: disable=too-few-public-methods
    """A maven proxy"""

    def __init__(self, config):
        self.logger = config['logger']
        self.config = config
        self.key = 'm2'
        if self.key not in self.config:
            self.config[self.key] = {
                'registry': 'https://repo.maven.apache.org/maven2'}

        self._proxy = Proxy(__name__, self.config[self.key], self.config)
        self.logger.debug('MavenProxy instantiated with %s',
                          self.config[self.key])

    @cherrypy.expose
    def proxy(self, environ, start_response):
        """Proxy a maven request."""
        path = environ["REQUEST_URI"].removeprefix("/m2")
        self.logger.debug('%s %s m2(%s)', __name__,
                          cherrypy.request.method, path)

        newpath = path

        newrequest = {}

        newrequest['content_type'] = self._proxy.mimetype(
            path, 'application/octet-stream')
        newrequest['method'] = cherrypy.request.method
        newrequest['path'] = newpath
        newrequest['headers'] = cherrypy.request.headers
        newrequest['storage'] = 'maven'
        newrequest['actual_request'] = cherrypy.request
        newrequest['logger'] = self.logger

        return self._proxy.proxy(newrequest, start_response)
