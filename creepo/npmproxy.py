"""An npm proxy"""
import io
import json

from urllib.parse import urlparse
import urllib3

import mime

import cherrypy

from httpproxy import HttpProxy


class NpmProxy:  # pylint: disable=fixme
    """The npm proxy"""

    def __init__(self, config):
        self.logger = config['logger']
        self.config = config
        self.key = "npm"
        if self.key not in self.config:
            self.config[self.key] = {'registry': 'https://registry.npmjs.org'}

        self._proxy = HttpProxy(self.config, self.key)
        self.logger.debug('NpmProxy instantiated with %s',
                          self.config[self.key])

    def callback(self, _input_bytes, request):
        """callback - preprocess the file before saving it"""

        data = json.load(io.BytesIO(_input_bytes))

        for version in data['versions']:
            dist = data['versions'][version]['dist']
            if dist:
                tarball = dist['tarball']
                if tarball:
                    # Point the client back to us for resolution.
                    new_tarball = urllib3.util.Url(
                        scheme='https',
                        host='localhost',   # TODO: get the listening public ip from config
                        port=self.config['port'],
                        path="/npm/tarballs/",
                        query=tarball,
                    )
                    data['versions'][version]['dist']['tarball'] = str(
                        new_tarball)
                else:
                    self.logger.warning(
                        '%s Did not find tarball for %s', __name__, version)
            else:
                self.logger.warning(
                    '%s Did not find dist for %s', __name__, version)
        request['response'] = bytes(json.dumps(data), 'utf-8')

    @cherrypy.expose
    def proxy(self, environ, start_response):
        '''Proxy an npm request.'''
        path = environ["REQUEST_URI"].removeprefix(f"/{self.key}")
        newpath = path

        newrequest = {}
        if len(mime.Types.of(path)) > 0:
            newrequest['content_type'] = mime.Types.of(path)[
                0].content_type

        newrequest['method'] = cherrypy.request.method
        newrequest['headers'] = cherrypy.request.headers
        newrequest['actual_request'] = cherrypy.request

        if len(path.split('?')) == 2:
            new_remote = urlparse(path.split('?')[1])
            newrequest['storage'] = f"{self.key}/tarballs"
            # The base proxy will remove the prefix
            newrequest['path'] = new_remote.path
            new_host = f"{new_remote.scheme}://{new_remote.netloc}"
            self.logger.info(
                '%s Create new proxy with host %s and path %s', __name__, new_host, new_remote.path)
            print(
                f"type(new_remote.path) is {type(new_remote.path)} {new_remote.path}")
            dynamic_proxy = HttpProxy(
                self._proxy.dynamic_config(new_host), self.key)

            return dynamic_proxy.rest_proxy(newrequest, start_response)

        newrequest['path'] = newpath
        newrequest['storage'] = 'npm'
        newrequest['content_type'] = 'application/octet-stream'
        self.logger.info('%s Requesting file %s', __name__, newpath)
        newrequest['logger'] = self._proxy.logger
        newrequest['callback'] = self.callback
        return self._proxy.rest_proxy(newrequest, start_response)
