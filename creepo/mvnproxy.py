"""
Apache maven - proxy https://repo.maven.apache.org/maven2 for use by java, scala, gradle, and other developers
"""
import cherrypy

from httpproxy import Proxy


class MavenProxy:
    """A maven proxy"""

    def __init__(self, config, logger):
        self.logger = logger
        self.config = config
        self.key = 'm2'
        if self.key not in self.config:
            self.config[self.key] = {
                'registry': 'https://repo.maven.apache.org/maven2'}

        self.proxy = Proxy(__name__, self.config[self.key], self.config)
        self.logger.debug('MavenProxy instantiated with %s',
                          self.config[self.key])

    @cherrypy.expose
    def m2(self, environ, start_response):
        """Proxy a maven request."""
        path = environ["REQUEST_URI"].removeprefix("/m2")
        self.logger.debug('%s %s m2(%s)', __name__,
                          cherrypy.request.method, path)

        newpath = path
        if cherrypy.request.query_string != '':
            newpath = f"{newpath}?{cherrypy.request.query_string}"

        newrequest = {}

        newrequest['content_type'] = self.proxy.mimetype(
            path, 'application/octet-stream')
        newrequest['method'] = cherrypy.request.method
        newrequest['path'] = newpath
        newrequest['headers'] = cherrypy.request.headers
        newrequest['storage'] = 'maven'
        newrequest['actual_request'] = cherrypy.request

        return self.proxy.proxy(newrequest, None, start_response, self.logger)
