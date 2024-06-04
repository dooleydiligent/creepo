"""
A simple proxy which does no callback.

This class supports docker, maven, and apk proxies

"""
import mime
from urllib3._collections import HTTPHeaderDict
import cherrypy

from httpproxy import HttpProxy


class SimpleProxy(HttpProxy):  # pylint: disable=too-few-public-methods
    """
    A simple proxy for use with any repository which implements a simple REST interface, 
    such as maven and apk.  In the current code it is also used for docker, although
    docker requires a global kludge (docker must only be mounted at /v2)

    :param config: The global Creepo config

    :param key: The storage key prefix.  The key is also the @cherrypy.expose endpoint, below

    """

    def __init__(self, config, key):
        super().__init__(config, key)

        self.config[self.key] = config[key]

        # self.rest_proxy = HttpProxy(self, self.config[self.key], self.config)
        self.logger.debug('SimpleProxy instantiated with storage key %s and url %s',
                          key, config[key]['registry'])

    @cherrypy.expose
    def proxy(self, environ, start_response):
        """
        Proxy a request

        :param environ: The CherryPy request object

        :param start_response: The WSGI callback

        """
        # An exception for docker
        path = environ["REQUEST_URI"]
        if self.key != 'v2':
            path = path.removeprefix(f"/{self.key}")

        self.logger.debug('%s %s proxy(%s)', __name__,
                          cherrypy.request.method, environ)

        newpath = path

        headers = {}
        if 'HTTP_USER_AGENT' in environ:
            headers['User-Agent'] = environ['HTTP_USER_AGENT']
        if 'HTTP_ACCEPT' in environ:
            headers['Accept'] = environ['HTTP_ACCEPT']
        if 'HTTP_ACCEPT_ENCODING' in environ:
            headers['Accept-Encoding'] = environ['HTTP_ACCEPT_ENCODING']

        newrequest = {}

        if 'Content-Type' in environ:
            headers['content_type'] = environ['Content-Type']

        if not 'content_type' in headers:
            if len(mime.Types.of(path)) > 0:
                headers['content_type'] = mime.Types.of(path)[
                    0].content_type
            else:
                headers['content_type'] = 'application/json'

        headers['Content-Type'] = headers['content_type']
        
        newrequest['content_type'] = headers['content_type']
        newrequest['method'] = cherrypy.request.method
        newrequest['path'] = newpath
        newrequest['headers'] = HTTPHeaderDict(headers)
        newrequest['storage'] = self.key
        newrequest['actual_request'] = cherrypy.request
        self.logger.debug('%s %s', __name__, newrequest)
        newrequest['logger'] = self.logger
        return self.rest_proxy(newrequest, start_response)
