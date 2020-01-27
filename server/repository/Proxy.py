from werkzeug.wrappers import Response

from flask import request
from flask import make_response

import os
import requests
import urllib3
import shutil
# https://github.com/pallets/werkzeug/blob/master/src/werkzeug/wrappers/base_request.py

class Proxy(object):
  def __init__(self, type, upstream):
    self._type = type
    self._upstream = upstream
    self._upstream_url = urllib3.util.parse_url(upstream)
    if os.environ.get('CREEPO_BASE') is not None:
      self._creepo = os.environ.get('CREEPO_BASE')
    else:
      self._creepo = os.path.join(os.environ.get('HOME'), '.CREEPO_BASE')
    self._creepo = os.path.join(self._creepo, type)
    # Destroy the repo during development
    if self._creepo.startswith('/home/lane/.CREEPO_BASE'):
      if os.path.exists(self._creepo):
        shutil.rmtree(self._creepo)
    else:
      sys.exit(-1)
    if not os.path.exists(self._creepo):
      print('Creating repo for {name} at {base}'.format(name=type, base=self._creepo))
      os.makedirs(self._creepo)

  @property
  def hostname(self):
    return self._upstream_url.hostname

  @property
  def method(self):
    return self._method

  @property
  def url(self):
    return self._url

  @property
  def type(self):
    return self._type
  
  @property
  def query(self):
    return self._query
  
  @property
  def filename(self):
    return self._filename

  def proxy(self, request, callback):
    cached_file = os.path.join(self._creepo, os.path.join(request['storage'], request['path']))
    print('Searching for CACHED FILE: {cached_file}'.format(cached_file=cached_file))

    self._filename = cached_file

    http = urllib3.PoolManager()

    if not os.path.exists(cached_file):
      source_url = '{baseurl}{path}'.format(baseurl=self._upstream, path=request['path'])
      print('proxying {request_method} {source_url}'.format(request_method=request['method'], source_url=source_url))

      headers = {k: v for k, v in request['headers'].items()}
      headers['Host'] = '{host}'.format(host=self._upstream_url.hostname)

      splitpath = cached_file.split('/')
      file_name = splitpath.pop()
      file_path = '/'.join(splitpath)

      if file_path:
        if not os.path.exists(file_path):
          print('Creating folder(s) {folders}'.format(folders=file_path))
          os.makedirs(file_path)
          
      if os.path.isdir(cached_file):
        cached_file = '{oh_crap}'.format(oh_crap=os.path.join(cached_file, '...'))
      with http.request('GET', source_url, preload_content=False) as r, open(cached_file, 'wb') as out_file:
        shutil.copyfileobj(callback(r), out_file)

    # Returned the cached file
    print('returning cached file {file}'.format(file=cached_file))
    f = open(cached_file, 'rb')
    response = make_response(Response(f))

    return response