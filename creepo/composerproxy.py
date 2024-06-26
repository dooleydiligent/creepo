"""

Composer - proxy https://packagist.org for use by php developers

"""
import io
import json
import urllib.parse
from urllib.parse import urlparse
import cherrypy

from httpproxy import HttpProxy


class ComposerProxy:
    """
    Default configuration: { 'registry' : 'https://packagist.org' }

    Exposed at endpoint /p2

    When no_cache is not True then we will host selected 'source' and 'dist' packages

    Configure a project to use Creepo by adding this to composer.json:

.. code-block:: json

     {
       "repositories": [
          {
            "type": "composer",
            "url": "https://${HOST_IP}:4443/p2/"
          }
       ],
     }
    """

    def __init__(self, config):
        self.logger = config['logger']
        self.config = config
        self.key = 'p2'
        if not 'server' in config:
            config['server'] = 'localhost'
        if not 'port' in config:
            config['port'] = 4443

        if self.key not in self.config:
            self.config[self.key] = {
                'registry': 'https://packagist.org', 'self': f"https://{self.config['server']}:{self.config['port']}/p2"}

        self._proxy = HttpProxy(self.config, self.key)
        self.logger.debug('ComposerProxy instantiated with %s',
                          self.config[self.key])

    def callback(self, _input_bytes, request):
        """
        When ComposerProxy acts as a registry it will retrieve meta-data from the configured 
        upstream proxy.

        If no_cache is not True then the source and dist urls of the meta-data are re-written 
        to self-relative urls

        """
        self.logger.debug('%s received type(%s) as %s ',
                          __name__, type(_input_bytes), _input_bytes)
        data = json.load(io.BytesIO(_input_bytes))

        for package in data['packages']:
            self.logger.debug('%s package is %s', __name__, package)
            for version in data['packages'][package]:
                if version.get('source') is not None:
                    version['source']['url'] = self.config[self.key]['self'] + \
                        '/source?q=' + \
                        urllib.parse.quote_plus(version['source']['url'])
                if version.get('dist') is not None:
                    version['dist'][
                        'url'] = self.config[self.key]['self'] + \
                        '/dist?q=' + \
                        urllib.parse.quote_plus(version['dist']['url'])

        request['response'] = bytes(json.dumps(data), 'utf-8')

    @cherrypy.expose
    def proxy(self, environ, start_response):
        """
        Proxy a composer request.

        Creepo exposes a WSGI-compliant server at /p2
        """
        path = environ["REQUEST_URI"]
        if path == f"/{self.key}/packages.json":
            path = environ["REQUEST_URI"].removeprefix(f"/{self.key}")

        self.logger.debug('%s %s composer(%s)', __name__,
                          cherrypy.request.method, path)

        newpath = path
        if cherrypy.request.query_string != '':
            self.logger.debug('%s QUERY_STRING: %s', __name__,
                              cherrypy.request.query_string)

        newrequest = {}
        newrequest['method'] = cherrypy.request.method
        newrequest['headers'] = {}
        newrequest['actual_request'] = cherrypy.request
        newrequest['logger'] = self.logger

        if len(newpath.split('?q=')) > 1:
            new_remote = urlparse(
                urllib.parse.unquote_plus(newpath.split('?q=')[1]))
            # Remove the leading / from the remaining path to get the storage bucket
            newrequest['storage'] = f"{newpath.split('?q=')[0][1:]}"
            newpath = new_remote.path
            if '?' not in newpath and '&' in newpath:
                newrequest['path'] = newpath.replace('&', '?', 1)
            else:
                newrequest['path'] = newpath
            dynamic_proxy = HttpProxy(self._proxy.dynamic_config(
                f"{new_remote.scheme}://{new_remote.netloc}"), self.key)

            self.logger.info(
                '%s Create new proxy with host %s and path %s', __name__,
                f"{new_remote.scheme}://{new_remote.netloc}", new_remote.path)

            newrequest['content_type'] = dynamic_proxy.mimetype(
                newpath.split('?')[0], 'text/html')
            return dynamic_proxy.rest_proxy(newrequest, start_response)

        newrequest['content_type'] = self._proxy.mimetype(
            path, 'application/octet-stream')

        newrequest['path'] = newpath
        newrequest['storage'] = self.key
        newrequest['callback'] = self.callback
        return self._proxy.rest_proxy(newrequest, start_response)
