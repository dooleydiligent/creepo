"""The pip proxy"""
from urllib.parse import urlparse
import lxml.etree as ET

import cherrypy

from httpproxy import Proxy


class PipProxy:
    """The pip proxy"""

    def __init__(self, config, logger):
        self.logger = logger
        self.config = config
        self.key = 'pip'
        if self.key not in self.config:
            self.config[self.key] = {
                'registry': 'https://pypi.org/simple', 'self': 'https://localhost:4443/pip'}

        self.proxy = Proxy(__name__, self.config[self.key], self.config)
        self.logger.debug('PipProxy instantiated with %s',
                          self.config[self.key])

    def callback(self, _input_bytes, request):
        """write the file to disk"""
        parser = ET.XMLParser(recover=True)
        doc = _input_bytes
        tree = ET.fromstring(doc, parser=parser)

        if tree is not None:
            for node in tree.findall('.//a[@href]'):
                href = node.get('href')
                if href.find('/packages/') > -1:
                    new_tarball = urlparse(
                        href
                    )
                    newhref = f"{self.config['pip']['self']}{new_tarball.path}"
                    node.set('href', newhref)
            doc = ET.tostring(tree)

        request['response'] = doc

    @cherrypy.expose
    def pip(self, environ, start_response):
        '''Proxy a pip repo request.'''
        path = environ["REQUEST_URI"].removeprefix("/pip")
        self.logger.info('%s The request.uri is %s', __name__, path)

        newrequest = {}
        newrequest['method'] = cherrypy.request.method
        newrequest['headers'] = cherrypy.request.headers
        newrequest['actual_request'] = cherrypy.request
        # application/vnd.pypi.simple.v1+json, application/vnd.pypi.simple.v1+html, and text/html

        newrequest['content_type'] = 'application/vnd.pypi.simple.v1+html'
        newrequest['path'] = path

        if path.startswith('/packages'):
            newrequest['storage'] = 'npm/tarballs'
            newhost = 'https://files.pythonhosted.org'
            self.logger.info(
                '%s Create new proxy with host %s and path %s', __name__, newhost, path)
            dynamic_proxy = Proxy(__name__, {'registry': newhost}, self.config)
            return dynamic_proxy.proxy(newrequest, None, start_response, self.logger)

        newrequest['storage'] = self.key
        newrequest['logger'] = self.logger
        newrequest['callback'] = self.callback
        return self.proxy.proxy(newrequest, start_response)
