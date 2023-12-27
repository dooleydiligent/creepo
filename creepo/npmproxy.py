"""An npm proxy"""
import io
import json

from urllib.parse import urlparse
import urllib3

import mime

import cherrypy

from httpproxy import Proxy


class NpmProxy:  # pylint: disable=fixme
    """The npm proxy"""

    def __init__(self, config, logger):
        self.logger = logger
        self.config = config
        self.key = "npm"
        if self.key not in self.config:
            self.config[self.key] = {'registry': 'https://registry.npmjs.org'}

        self.proxy = Proxy(__name__, self.config[self.key], self.config)
        self.logger.debug('NpmProxy instantiated with %s',
                          self.config[self.key])

    def noopcallback(self, _input_bytes, request):
        """noopcallback"""
        self.logger.debug('%s noopcallback for %s',
                          __name__, request)
        self.proxy.persist(_input_bytes, request, self.logger)

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

        content = json.dumps(data)
        self.proxy.persist(bytes(content, encoding="utf-8"),
                           request, self.logger)

    @cherrypy.expose
    def npm(self, environ, start_response):
        '''Proxy an npm request.'''
        path = environ["REQUEST_URI"].removeprefix("/npm")
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
            newrequest['storage'] = 'npm/tarballs'
            newrequest['path'] = new_remote.path
            newhost = f"{new_remote.scheme}://{new_remote.netloc}"
            self.logger.info(
                '%s Create new proxy with host %s and path %s', __name__, newhost, new_remote.path)
            dynamic_proxy = Proxy(__name__, {'registry': newhost}, self.config)
            return dynamic_proxy.proxy(newrequest, self.noopcallback, start_response, self.logger)

        newrequest['path'] = newpath
        newrequest['storage'] = 'npm'
        newrequest['content_type'] = 'application/octet-stream'
        self.logger.info('%s Requesting file %s', __name__, newpath)
        return self.proxy.proxy(newrequest, self.callback, start_response, self.logger)
