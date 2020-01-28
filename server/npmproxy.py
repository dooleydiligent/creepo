from bottle import Bottle, request, route, run

import io
import json
import lxml.etree as ET
import os
import requests
import tempfile
import urllib3

# from auth import login_required
# from db import get_db

# from file_like import IOInterface
from repository.Proxy import Proxy

# bp = Blueprint('npmproxy', __name__, url_prefix='/npm')
# print('registering {proxy}'.format(proxy=bp.url_prefix))
app = Bottle()
print('registering /npm')
# Proxy all requests to upstreamurl
#proxy = Proxy(__name__, 'https://registry.npmjs.org/')
proxy = Proxy(__name__, 'http://localhost:8081/repository/npm/')

def before_request(path, url):
  print('before_request({path}, {url})'.format(path=path, url=url))
  return url

def after_request(url, response):
  print('after_request({url})'.format(url=url))

def make_self_relative(tarball):
  # parse tarball to a url
  # make host and protocol self-relative
  url = urllib3.util.parse_url(tarball)
  url_as_string = url
  return url_as_string

def noopcallback(input, original_request):
  print('noopcallback')
  with tempfile.NamedTemporaryFile(delete=False) as temp:
    print('tempfile name is {name}'.format(name=temp.name))
    temp.write(input.read())
    temp.flush()
  print('wrote tempfile')
  f = open(temp.name, 'rb')
  return f
        
def callback(input, original_request):
  print('callback {cb}'.format(cb=`callback`))
  # rewrite the file before sending it
  # Consider adding an extension that is a timestamp.
  # If a future request is TTL time after the last request then return it

  data = json.load(input)
  package_name = data['name']
  print('finished loading {filename} for {package}'.format(filename=proxy.filename, package=package_name))
  for version in data['versions']:
    dist = data['versions'][version]['dist']
    if dist:
      print('found version[{version}].dist'.format(version=version))
      tarball = dist['tarball']
      if tarball:
        print('found version {v} tarball {t}'.format(v=version, t=tarball))
        # Replace the tarball with a value that points back to yourself
        relevant_parts = -3
        if package_name.startswith('@'):
          relevant_parts = -4
        last_three = '/'.join(tarball.split('/')[relevant_parts:])
        print('last_threeOrFour is {last_three}'.format(last_three=last_three))
        new_tarball = urllib3.util.Url(scheme='http', host='localhost', port=5000, path='/npm/tarballs/{path}'.format(path=last_three))
        data['versions'][version]['dist']['tarball'] = str(new_tarball)
        print('Changed tarball url from {f} to {newurl}'.format(f=tarball, newurl=new_tarball))
      else:
        print('did not find tarball for {v}'.format(v=version))
    else:
      print('did not find dist for {v}'.format(v=version))

  with tempfile.NamedTemporaryFile(delete=False) as temp:
    print('tempfile name is {name}'.format(name=temp.name))
    temp.write(json.dumps(data).decode('utf-8'))
    temp.flush()
  f = open(temp.name, 'rb')
  return f

@app.route('/<path:path>')
def index(path):
    '''Proxy a repo request.'''
    print('The request.url is {url}'.format(url=request.url))
    newpath = '{path}'.format(path=path)
    print('newpath is {np}'.format(np=newpath))  

    if request.query_string != '':
      newpath = '{newurl}?{query}'.format(newurl=newpath,query=request.query_string)

    method = request.method
    newrequest = dict()
    newrequest['method'] = request.method
    newrequest['headers'] = request.headers
    newrequest['actual_request'] = request
    actual_callback = noopcallback
    if path.startswith('tarballs'):
      newrequest['storage'] = 'npm/tarballs'
      newrequest['path'] = '/'.join(newpath.split('/')[1:])
    else:
      newrequest['storage'] = 'npm'
      newrequest['path'] = newpath
      actual_callback = callback

    resp = proxy.proxy(newrequest, actual_callback)  
    after_request(path, resp)

    # resp = make_response(proxy)
    # Consider replacing resp.headers
    return resp