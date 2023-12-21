import cherrypy
import lxml.etree as ET
import mime
import os
import requests
import tempfile

from Proxy import Proxy

class MavenProxy:
  def __init__(self):
    cherrypy.log('MavenProxy instantiated')
    self.maven = Proxy(__name__, os.environ.get('MAVEN_PROXY', 'https://repo.maven.apache.org/maven2'))

  def callback(self, input, outpath):
    cherrypy.log('callback: {file}'.format(file=outpath))
    content = input.read()
    input.close()
    outfile = open(outpath, 'wb')
    outfile.write(content)
    outfile.close()
    input.close()
    cherrypy.log('wrote {count} byte(s) to {file}'.format(count=len(content), file=outpath))

  @cherrypy.expose
  def m2(self, environ, start_response):
    '''Proxy a maven request.'''
    self.status = 200
    path = environ["REQUEST_URI"].removeprefix("/m2")
    cherrypy.log('{method} m2({path})'.format(method=cherrypy.request.method, name=__name__, path=path))

    newpath = '{path}'.format(path=path)
    if cherrypy.request.query_string != '':
      newpath = '{newurl}?{query}'.format(newurl=newpath,query=cherrypy.request.query_string)

    method = cherrypy.request.method
    newrequest = dict()
    if len(mime.Types.of(path)) > 0:
      newrequest['content_type'] = mime.Types.of(path)[0].content_type

    newrequest['method'] = cherrypy.request.method
    newrequest['path'] = newpath
    newrequest['headers'] = cherrypy.request.headers
    newrequest['storage'] = 'maven'
    newrequest['actual_request'] = cherrypy.request
        
    return self.maven.proxy(newrequest, self.callback, start_response)
