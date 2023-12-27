"""

Composer - proxy https://packagist.org for use by php developers

"""
import io
import json
import urllib.parse
from urllib.parse import urlparse

import cherrypy

from httpproxy import Proxy


class ComposerProxy:
    """

    Default configuration: { 'registry' : 'https://packagist.org' }
    
    Exposed at endpoint /p2

    When no_cache is not True then we will host selected 'source' and 'dist' packages

    Configure a project to use Creepo by adding this to composer.json:

    ```
    "repositories": [
    {
        "type": "composer",
        "url": "https://${HOST_IP}:4443/p2/"
    },
    {
        "packagist.org": false
    }
    ],

    ```

    """

    def __init__(self, config, logger):
        self.logger = logger
        self.config = config
        self.key = 'p2'
        if self.key not in self.config:
            self.config[self.key] = {
                'registry': 'https://packagist.org', 'self': 'https://localhost:4443/p2'}

        self.proxy = Proxy(__name__, self.config[self.key], self.config)
        self.logger.debug('ComposerProxy instantiated with %s',
                          self.config[self.key])

    def noopcallback(self, _input_bytes, request):
        """
        When ComposerProxy retrieves source and dist packages on behalf of a client,
        these will be persisted if no_cache is not True.
        """
        self.logger.debug('%s noopcallback for %s', __name__, request['output_filename'])
        self.proxy.persist(_input_bytes, request, self.logger)

    def callback(self, _input_bytes, request):
        """
        When ComposerProxy acts as a registry it will retrieve meta-data from the configured 
        upstream proxy.

        If no_cache is not True then the source and dist urls of the meta-data are re-written 
        to self-relative urls

        """

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

        content = json.dumps(data)
        self.proxy.persist(bytes(content, encoding="utf-8"),
                           request, self.logger)

    @cherrypy.expose
    def p2(self, environ, start_response):
        """
        Proxy a composer request.
        
        Creepo exposes a WSGI-compliant server at /p2
        """
        path = environ["REQUEST_URI"]
        if path == '/p2/packages.json':
            path = environ["REQUEST_URI"].removeprefix("/p2")

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

            dynamic_proxy = Proxy(
                __name__, {'registry': f"{new_remote.scheme}://{new_remote.netloc}"}, self.config)

            self.logger.info(
                '%s Create new proxy with host %s and path %s', __name__,
                f"{new_remote.scheme}://{new_remote.netloc}", new_remote.path)

            newrequest['content_type'] = dynamic_proxy.mimetype(
                newpath.split('?')[0], 'text/html')
            return dynamic_proxy.proxy(newrequest, self.noopcallback, start_response, self.logger)

        newrequest['content_type'] = self.proxy.mimetype(
            path, 'application/octet-stream')

        newrequest['path'] = newpath
        newrequest['storage'] = self.key

        return self.proxy.proxy(newrequest, self.callback, start_response, self.logger)
