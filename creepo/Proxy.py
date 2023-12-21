import cherrypy
import mime
import os
import requests
import urllib3
import shutil

class Proxy(object):
  def __init__(self, type, upstream):
    self._type = type
    self._upstream = upstream
    self._upstream_url = urllib3.util.parse_url(upstream)
    if os.environ.get('CREEPO_BASE') is not None:
      self._creepo = os.environ.get('CREEPO_BASE')
    else:
      self._creepo = os.path.join(os.environ.get('HOME'), '.CREEPO_BASE')

  @property
  def type(self):
    return self._type
  
  @property
  def filename(self):
    return self._filename

  def proxy(self, request, callback, start_response):
    if self._creepo is None or self._creepo == "":
      panic("This cannot be")
    if not os.path.exists(self._creepo):
      os.makedirs(self._creepo)

    cached_file = '{creepo}/{storage}{path}'.format(creepo=self._creepo, storage=request['storage'], path=request['path'])

    self._method = request['method']
    self._filename = cached_file
    contentType = request['headers'].get('content-type')
    if contentType is None:
      contentType = request.get('content_type', None)
    if contentType is None and len(mime.Types.of(request['path'])) > 0:
      contentType = mime.Types.of(request['path'])[0].content_type
    if contentType is None:
      contentType = "octet/stream"

    if not os.path.exists(self._filename):
      cherrypy.log('Requesting file {file}'.format(file=request['path']))
      http = urllib3.PoolManager()
      resp = dict()

      headers = {}
      headers['Host'] = '{host}'.format(host=self._upstream_url.hostname)
      headers['content-type'] = contentType

      source_url = '{baseurl}{path}'.format(baseurl=self._upstream, path=request['path'])

      splitpath = cached_file.split('/')
      file_name = splitpath.pop()
      file_path = '/'.join(splitpath)

      if file_path:
        if not os.path.exists(file_path):
          cherrypy.log('Creating folder(s) {folders}'.format(folders=file_path))
          try:
            os.makedirs(file_path)
          except:
            if e.errno != os.errno.EEXIST:
              raise
            pass
        cherrypy.log('The actual request for file {file}'.format(file=request['path']))
        with http.request('GET', source_url, preload_content=False, headers=headers) as r, open(cached_file, 'wb') as out_file:
          if r.status < 400:
            callback(r, cached_file)
          else:
            cherrypy.log('response.status is {status} for {file}'.format(status=r.status, file=request['path']))
      else:
        panic('There is no file_path and file_name is {file_name}'.format(file_name=file_name))

    if os.path.exists(cached_file):
      infile = open(cached_file, 'rb')
      content = infile.read()
      infile.close()
      start_response('200 OK', [('Content-Type', contentType)])
      yield content
    else:
      start_response('404 Not Found', [('Content-Type', 'text/html')])
      yield []
