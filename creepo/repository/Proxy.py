import logging
from bottle import BaseResponse, Bottle, response, route, run

import os
import requests
import urllib3
import shutil
# https://github.com/pallets/werkzeug/blob/master/src/werkzeug/wrappers/base_request.py

from creepo.repository.Logger import Logger

logger = Logger(__name__)

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
    # if self._creepo.startswith('/home/lane/.CREEPO_BASE'):
    #   if os.path.exists(self._creepo):
    #     shutil.rmtree(self._creepo)
    # else:
    #   logger.warn('unexpected _creepo {_creepo}'.format(_creepo=self._creepo))
    #   sys.exit(-1)
    if not os.path.exists(self._creepo):
      logger.debug('Creating repo for {name} at {base}'.format(name=type, base=self._creepo))
      os.makedirs(self._creepo)

  @property
  def type(self):
    logger.debug('@property type() = {type}'.format(type=self._type))
    return self._type
  
  @property
  def filename(self):
    logger.debug('@property filename() = {filename}'.format(filename=self._filename))
    return self._filename

  def proxy(self, request, callback):
    logger.debug('proxy request = {request}'.format(request=request))
    logger.debug('request content-type and accept are {content_type} / {accept}'.format(content_type=request['headers'].get('content-type'), accept=request['headers'].get('accept')))

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
    if contentType is None:
      contentType = request['content_type']
    if contentType is None:
      contentType = request['headers'].get('accept')
      logger.debug('Accept header is {accept}'.format(accept=contentType))
    logger.debug('content-type header will be {ct}'.format(ct=contentType))

    if not os.path.exists(cached_file):
      source_url = '{baseurl}{path}'.format(baseurl=self._upstream, path=request['path'])
      logger.debug('proxying {request_method} {source_url}'.format(request_method=request['method'], source_url=source_url))

      splitpath = cached_file.split('/')
      file_name = splitpath.pop()
      file_path = '/'.join(splitpath)

      if file_path:
        if not os.path.exists(file_path):
          logger.debug('Creating folder(s) {folders}'.format(folders=file_path))
          try:
            os.makedirs(file_path)
          except:
            if e.errno != os.errno.EEXIST:
              raise
            pass
          
      if os.path.isdir(cached_file):
        logger.debug('Create ... file at {path}'.format(path=cached_file))
        cached_file = '{cached_file}'.format(cached_file=os.path.join(cached_file, '...'))
        
      with http.request('GET', source_url, preload_content=False, headers={ 'content-type': contentType}) as r, open(cached_file, 'wb') as out_file:
        logger.debug('response.status is actually {status}'.format(status=r.status))
        if r.status < 400:
          cached_file = callback(r, cached_file)
          # Response is now just a file path
          logger.debug('response.status is {status}'.format(status=r.status))
          # shutil.copyfileobj(response, out_file)
          # response.close()
          logger.debug('Response content-type is {content_type}'.format(content_type=r.headers.get('content-type')))
#          headers = r.headers
#          contentType = r.headers.get('content-type')
        else:
          logger.warn('Response status {status} requesting {url}'.format(status=r.status, url=source_url))
          cached_file = None
#          return r
        r.close()

    # Return the path to the file or nothing
    return cached_file
    # # Returned the cached file
    # logger.debug('returning cached file {file}'.format(file=cached_file))
    # f = open(cached_file, 'rb')
    # resp['content'] = f.read()

    # br = BaseResponse(body=resp['content'], status='200 OK', headers={ 'content-type': contentType})
    # logger.debug('response content is {content_type}: {content}'.format(content_type=contentType, content=resp['content']))
    # return br