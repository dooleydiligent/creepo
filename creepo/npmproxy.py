from bottle import Bottle, request, route, run

import io
import json
import lxml.etree as ET
import os
import requests
import tempfile
import urllib3

from creepo.repository.Logger import Logger
from creepo.repository.Proxy import Proxy

logger = Logger(__name__)
logger.debug('registering {name}'.format(name=__name__))

app = Bottle()
proxy = Proxy(__name__, os.environ.get('NPM_PROXY', 'https://registry.npmjs.org'))
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
  for version in data['versions']:
    dist = data['versions'][version]['dist']
    if dist:
      tarball = dist['tarball']
      if tarball:
        # Replace the tarball with a value that points back to yourself
        relevant_parts = -3
        if package_name.startswith('@'):
          relevant_parts = -4
        last_three = '/'.join(tarball.split('/')[relevant_parts:])
        new_tarball = urllib3.util.Url(scheme='http', host='localhost', port=5000, path='/npm/tarballs/{path}'.format(path=last_three))
        data['versions'][version]['dist']['tarball'] = str(new_tarball)
      else:
        logger.debug('did not find tarball for {v}'.format(v=version))
    else:
      logger.debug('did not find dist for {v}'.format(v=version))

  content = json.dumps(data)

  outfile = open(outpath, 'wb')
  outfile.write(content.encode(encoding='utf-8', errors='strict'))
  outfile.close()
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
