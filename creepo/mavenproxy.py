from bottle import BaseResponse, Bottle, request, route, run

import lxml.etree as ET
import os
import requests
import tempfile

from repository.Proxy import Proxy
from repository.Logger import Logger

app = Bottle()
# Proxy all requests to upstreamurl
#maven = Proxy(__name__, 'https://repo.maven.apache.org/maven2')
maven = Proxy(__name__, 'http://localhost:8081/repository/PUBLIC/')
logger = Logger(__name__)
def callback(input, outpath):
  logger.debug('callback: save the response to a local file')
  content = input.read()
  input.close()
  outfile = open(outpath, 'wb')
  outfile.write(content)
  outfile.close()
  logger.debug('wrote {file}'.format(file=outpath))
  return outpath
#  f = open(outpath, 'rb')
#  return f

@app.route('/<path:path>')
def index(path):
  '''Proxy a maven request.'''

  logger.debug('{method} {name}.index({path})'.format(method=request.method, name=__name__, path=path))
  newpath = '{path}'.format(path=path)
  if request.query_string != '':
    newpath = '{newurl}?{query}'.format(newurl=newpath,query=request.query_string)

  method = request.method
  newrequest = dict()
  newrequest['method'] = request.method
  newrequest['path'] = newpath
  newrequest['headers'] = request.headers
  newrequest['storage'] = 'maven'
  newrequest['actual_request'] = request
  newrequest['content_type'] = 'application/xml'
  resp = maven.proxy(newrequest, callback)

#  logger.debug('Response content-type is {content_type}'.format(content_type=resp.headers.get('content-type')))
#  # Consider replacing resp.headers
#  logger.debug('resp.status is {status}'.format(status=resp.status))
#  logger.debug('resp.content is {content}'.format(content=resp.body))
#  return BaseResponse(body=resp.body, status=resp.status, headers={ 'content-type': resp.headers.get('content-type')})
  content = None
  status = 404
  if resp:
    if os.path.exists(resp):
      status = 200
      outfile = open(resp, 'rb')
      content = outfile.read()
      outfile.close()
  return content