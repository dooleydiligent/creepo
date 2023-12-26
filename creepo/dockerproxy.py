"""A docker proxy"""
import mime

import cherrypy

from proxy import Proxy


class DockerProxy:
    """A docker proxy"""

    def __init__(self, config, logger):
        self.logger = logger
        self.config = config
        self.key = 'docker'
        if self.key not in self.config:
            self.config[self.key] = {
                'registry': 'https://registry-1.docker.io'}

        self.proxy = Proxy(__name__, self.config[self.key])
        self.logger.debug('DockerProxy instantiated with %s',
                          self.config[self.key])

    def callback(self, _input_bytes, _outpath):
        """A callback to write the file"""
        self.logger.debug('%s callback: %s', __name__, _outpath)
        self.proxy.persist(_input_bytes, _outpath, self.logger)

    @cherrypy.expose
    def v2(self, environ, start_response):
        """Proxy a docker request."""
        path = environ["REQUEST_URI"]
        self.logger.debug('%s %s v2(%s)', __name__,
                          cherrypy.request.method, environ)

        newpath = path
        if cherrypy.request.query_string != '':
            newpath = f"{newpath}?{cherrypy.request.query_string}"

        headers = {}
        headers['User-Agent'] = environ['HTTP_USER_AGENT']
        if environ.get('HTTP_ACCEPT') is not None:
            headers['Accept'] = environ['HTTP_ACCEPT']
        if environ.get('HTTP_ACCEPT_ENCODING') is not None:
            headers['Accept-Encoding'] = environ['HTTP_ACCEPT_ENCODING']

        newrequest = {}
        if len(mime.Types.of(path)) > 0:
            newrequest['content_type'] = mime.Types.of(path)[
                0].content_type
        else:
            newrequest['content_type'] = 'application/json'
        headers['Content-Type'] = newrequest['content_type']

        newrequest['method'] = cherrypy.request.method
        newrequest['path'] = newpath
        newrequest['headers'] = headers
        newrequest['storage'] = self.key
        newrequest['actual_request'] = cherrypy.request
        self.logger.debug('%s %s', __name__, newrequest)
        return self.proxy.proxy(newrequest, self.callback, start_response, self.logger)