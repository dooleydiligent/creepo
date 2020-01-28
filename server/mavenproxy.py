from bottle import Bottle, request, route, run

import lxml.etree as ET
import requests
import tempfile

from repository.Proxy import Proxy


app = Bottle()
# Proxy all requests to upstreamurl
#maven = Proxy(__name__, 'https://repo.maven.apache.org/maven2')
maven = Proxy(__name__, 'http://localhost:8081/repository/PUBLIC/')

def callback(input, original_request):
  # TODO: Have the caller suggest the local file path
  print('callback: save the response to a local file')
  content = input.read()

  with tempfile.NamedTemporaryFile(delete=False) as temp:
    print('tempfile name is {name}'.format(name=temp.name))
    temp.write(content)
    temp.flush()
  print('wrote tempfile')
  f = open(temp.name, 'rb')
  return f

@app.route('/<path:path>')
def index(path):
  '''Proxy a maven request.'''

  print('{method} {name}.index({path})'.format(method=request.method, name=__name__, path=path))
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
  resp = maven.proxy(newrequest, callback)
  # Consider replacing resp.headers
  return resp