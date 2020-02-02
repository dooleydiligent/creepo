from bottle import Bottle, request, route, run

import io
import json
import lxml.etree as ET
import os
import requests
import tempfile
import urllib3

from repository.Logger import Logger
from repository.Proxy import Proxy

# Proxy all requests to upstreamurl
#proxy = Proxy(__name__, 'https://registry.npmjs.org/')

logger = Logger(__name__)
logger.debug('registering {name}'.format(name=__name__))

app = Bottle()
proxy = Proxy(__name__, 'http://localhost:8081/repository/npm/')

def before_request(path, url):
  logger.debug('before_request({path}, {url})'.format(path=path, url=url))
  return url

def after_request(url, response):
  logger.debug('after_request({url})'.format(url=url))

def noopcallback(input, outpath):
  logger.debug('noopcallback for {filename}'.format(filename=outpath))

  outfile = open(outpath, 'wb')
  outfile.write(input.read())
  input.close()
  outfile.close()
  logger.debug('wrote {file}'.format(file=outpath))
  return outpath

def callback(input, outpath):
  logger.debug('callback {cb} for file {outpath}'.format(cb='callback', outpath=outpath))
  # rewrite the file before sending it
  # Consider adding an extension that is a timestamp.
  # If a future request is TTL time after the last request then return it

  data = json.load(input)
  input.close()
  package_name = data['name']
#  logger.debug('finished loading {filename} for {package}'.format(filename=proxy.filename, package=package_name))
  for version in data['versions']:
    dist = data['versions'][version]['dist']
    if dist:
#      logger.debug('found version[{version}].dist'.format(version=version))
      tarball = dist['tarball']
      if tarball:
#        logger.debug('found version {v} tarball {t}'.format(v=version, t=tarball))
        # Replace the tarball with a value that points back to yourself
        relevant_parts = -3
        if package_name.startswith('@'):
          relevant_parts = -4
        last_three = '/'.join(tarball.split('/')[relevant_parts:])
#        logger.debug('last_threeOrFour is {last_three}'.format(last_three=last_three))
        new_tarball = urllib3.util.Url(scheme='http', host='localhost', port=5000, path='/npm/tarballs/{path}'.format(path=last_three))
        data['versions'][version]['dist']['tarball'] = str(new_tarball)
#        logger.debug('Changed tarball url from {f} to {newurl}'.format(f=tarball, newurl=new_tarball))
      else:
        logger.debug('did not find tarball for {v}'.format(v=version))
    else:
      logger.debug('did not find dist for {v}'.format(v=version))

#  logger.debug('Writing content from package {name}'.format(name=package_name))
#  logger.debug('Content is [{content}]'.format(content=data))
  content = json.dumps(data)

  # with tempfile.NamedTemporaryFile(delete=False) as temp:
  #   logger.debug('tempfile name is {name}'.format(name=temp.name))
  #   temp.write(json.dumps(data).decode('utf-8'))
  #   temp.flush()
  # f = open(temp.name, 'rb')
  # return f
  outfile = open(outpath, 'wb')
  outfile.write(content.encode(encoding='utf-8', errors='strict'))
  outfile.close()
#  logger.debug('wrote {file}'.format(file=outpath))
  return outpath

@app.route('/<path:path>')
def index(path):
    '''Proxy a repo request.'''
    logger.debug('The request.url is {url}'.format(url=request.url))
    newpath = '{path}'.format(path=path)
    logger.debug('newpath is {np}'.format(np=newpath))  

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
    content = None
    status = 404
    if resp:
      if os.path.exists(resp):
        status = 200
        outfile = open(resp, 'rb')
        content = outfile.read()
        outfile.close()
    return content
    # # resp = make_response(proxy)
    # # Consider replacing resp.headers
    # return resp