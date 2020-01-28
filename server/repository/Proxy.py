import logging
from bottle import BaseResponse, Bottle, response, route, run

#from werkzeug.wrappers import Response

# from flask import request
# from flask import make_response

import os
import requests
import urllib3
import shutil
# https://github.com/pallets/werkzeug/blob/master/src/werkzeug/wrappers/base_request.py

#
# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)
#

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
      logger.debug('Creating repo for {name} at {base}'.format(name=type, base=self._creepo))
      os.makedirs(self._creepo)

  # @property
  # def hostname(self):
  #   return self._upstream_url.hostname

  # @property
  # def url(self):
  #   return self._url

  @property
  def type(self):
    return self._type
  
  # @property
  # def query(self):
  #   return self._query
  
  @property
  def filename(self):
    return self._filename

  def proxy(self, request, callback):
    actual_request = request['actual_request']
    cached_file = os.path.join(self._creepo, os.path.join(request['storage'], request['path']))
    logger.debug('Searching for CACHED FILE: {cached_file}'.format(cached_file=cached_file))

    self._method = request['method']
    self._filename = cached_file

    http = urllib3.PoolManager()
    resp = dict()
    rheaders = {}
    #{k: v for k, v in request['headers'].items()}
    headers = {}
    headers['Host'] = '{host}'.format(host=self._upstream_url.hostname)
    contentType = request['headers'].get('content-type')
    logger.debug('content-type header in the request is {ct}'.format(ct=contentType))
    if contentType is None:
      contentType = request['headers'].get('accept')
      logger.debug('Accept header is {accept}'.format(accept=contentType))

    if not os.path.exists(cached_file):
      source_url = '{baseurl}{path}'.format(baseurl=self._upstream, path=request['path'])
      logger.debug('proxying {request_method} {source_url}'.format(request_method=request['method'], source_url=source_url))

      splitpath = cached_file.split('/')
      file_name = splitpath.pop()
      file_path = '/'.join(splitpath)

      if file_path:
        if not os.path.exists(file_path):
          logger.debug('Creating folder(s) {folders}'.format(folders=file_path))
          os.makedirs(file_path)
          
      if os.path.isdir(cached_file):
        cached_file = '{oh_crap}'.format(oh_crap=os.path.join(cached_file, '...'))
        
      with http.request('GET', source_url, preload_content=False, headers={ 'content-type': contentType}) as r, open(cached_file, 'wb') as out_file:
        logger.debug('response.status is actually {status}'.format(status=r.status))
        if r.status < 400:
          response = callback(r, request)
          logger.debug('response.status is {status}'.format(status='200 OK'))
          shutil.copyfileobj(response, out_file)
          headers = r.headers
        else:
          logger.warn('Response status {status} requesting {url}'.format(status=r.status, url=source_url))
          return r

    # Returned the cached file
    logger.debug('returning cached file {file}'.format(file=cached_file))
    f = open(cached_file, 'rb')
    resp['content'] = f.read()

    br = BaseResponse(body=resp['content'], status='200 OK', headers={ 'content-type': contentType})
    return br