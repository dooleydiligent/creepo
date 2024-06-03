"""The pip proxy"""
from urllib.parse import urlparse
import lxml.etree as ET

import cherrypy

from httpproxy import HttpProxy


class PipProxy:
    """The pip proxy"""

    def __init__(self, config):
        self.logger = config['logger']
        self.config = config
        self.key = 'pip'
        if not 'server' in config:
            config['server'] = 'localhost'
        if not 'port' in config:
            config['port'] = 4443
            
        if self.key not in self.config:
            self.config[self.key] = {
                'registry': 'https://pypi.org/simple', 'self': f"https://{self.config['server']}:{self.config['port']}/pip"}

        self._proxy = HttpProxy(self.config, self.key)
        self.logger.debug('PipProxy instantiated with %s',
                          self.config[self.key])

    def callback(self, _input_bytes, request):
        """callback - preprocess the file"""
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
    def proxy(self, environ, start_response):
        '''Proxy a pip repo request.'''
        path = environ["REQUEST_URI"].removeprefix(f"/{self.key}")

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

            dynamic_config = {
                'no_cache': self._proxy.no_cache,
                'logger': self.config['logger'],
                f"{self.key}": {
                    'registry': newhost,
                }
            }
            dynamic_proxy = HttpProxy(dynamic_config, self.key)

            return dynamic_proxy.rest_proxy(newrequest, start_response)

        newrequest['storage'] = self.key
        newrequest['logger'] = self.logger
        newrequest['callback'] = self.callback
        return self._proxy.rest_proxy(newrequest, start_response)
