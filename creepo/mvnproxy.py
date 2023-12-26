"""A maven proxy"""
import mime

import cherrypy

from proxy import Proxy


class MavenProxy:
    """A maven proxy"""

    def __init__(self, config, logger):
        self.logger = logger
        self.config = config
        self.key = 'm2'
        if self.key not in self.config:
            self.config[self.key] = {
                'registry': 'https://repo.maven.apache.org/maven2'}

        self.proxy = Proxy(__name__, self.config[self.key])
        self.logger.debug('MavenProxy instantiated with %s',
                          self.config[self.key])

    def callback(self, _input_bytes, _outpath):
        """A callback to write the file"""
        self.logger.debug('%s callback: %s', __name__, _outpath)
        self.proxy.persist(_input_bytes, _outpath, self.logger)

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
        if len(mime.Types.of(path)) > 0:
            newrequest['content_type'] = mime.Types.of(path)[
                0].content_type
        else:
            newrequest['content_type'] = 'application/octet-stream'
        newrequest['method'] = cherrypy.request.method
        newrequest['path'] = newpath
        newrequest['headers'] = cherrypy.request.headers
        newrequest['storage'] = 'maven'
        newrequest['actual_request'] = cherrypy.request

        return self.proxy.proxy(newrequest, self.callback, start_response, self.logger)
