"""An npm proxy"""

import gzip
import io
import json

from urllib.parse import urlparse, unquote
import urllib3

import mime
import threading
import cherrypy

from httpproxy import HttpProxy


class NpmProxy:  # pylint: disable=fixme
    """The npm proxy"""

    def __init__(self, config):
        self.logger = config["logger"]
        self.config = config
        self.key = "npm"
        if self.key not in self.config:
            self.config[self.key] = {"registry": "https://registry.npmjs.org"}

        self._proxy = HttpProxy(self.config, self.key)
        self.logger.debug('NpmProxy instantiated with %s',
                          self.config[self.key])

    def callback(self, _input_bytes, request):
        """callback - preprocess the file"""
        data = ""
        if not 'content_type' in request:
            self.logger.warning(f"npm proxy callback: NO CONTENT-TYPE for request {request['path']}")
        else:
            if request['content_type'] != 'application/json':
                self.logger.info(f"npm proxy callbak: Unexpected content-type {request['content_type']} for request {request['path']}: Content:{_input_bytes}")

        data = json.load(io.BytesIO(_input_bytes))
        for version in data["versions"]:
            dist = data["versions"][version]["dist"]
            if dist:
                tarball = dist["tarball"]
                if tarball:
                    # Point the client back to us for resolution.
                    new_tarball = urllib3.util.Url(
                        scheme="https",
                        host=self.config["server"],
                        port=self.config["port"],
                        path="/npm/tarballs/",
                        query=tarball,
                    )
                    data["versions"][version]["dist"]["tarball"] = str(new_tarball)
                else:
                    self.logger.warning(
                        "%s Did not find tarball for %s", __name__, version
                    )
            else:
                self.logger.warning(
                    "%s Did not find dist for %s", __name__, version
                )
        request["response"] = bytes(json.dumps(data), "utf-8")


    @cherrypy.expose
    def proxy(self, environ, start_response):
        '''Proxy an npm request.'''
        self.logger.debug(f"npm: {environ['REQUEST_URI']}")
        path = environ["REQUEST_URI"].removeprefix(f"/{self.key}")
        newpath = path

        newrequest = {}
        if 'Content-Type' in environ:
            newrequest['content_type'] = environ['Content-Type']

        newrequest["method"] = cherrypy.request.method
        newrequest["headers"] = cherrypy.request.headers
        newrequest["actual_request"] = cherrypy.request
        newrequest["logger"] = self.logger

        if len(newpath.split('?')) == 2:
            # Don't set the callback because the result is not preprocessed
            new_remote = urlparse(unquote(newpath).split('?')[1])

            # The base proxy will remove the prefix
            newrequest['storage'] = f"{self.key}/tarballs"

            # It is not clear where this contamination occurs :(
            if new_remote.path.endswith("="):
                newrequest["path"] = new_remote.path[:-1]
            else:
                newrequest["path"] = new_remote.path

            new_host = f"{new_remote.scheme}://{new_remote.netloc}"
            self.logger.debug(
                '%s Create new proxy with host %s and path %s', __name__, new_host, new_remote.path)

            dynamic_proxy = HttpProxy(
                self._proxy.dynamic_config(new_host), self.key)

            return dynamic_proxy.rest_proxy(newrequest, start_response)

        newrequest['path'] = newpath
        newrequest['storage'] = 'npm'

        self.logger.debug('%s Requesting file %s', __name__, newpath)
        newrequest['callback'] = self.callback

        # Always refresh the package document (until ttl is implemented)
        newrequest["force_request"] = True
        return self._proxy.rest_proxy(newrequest, start_response)
