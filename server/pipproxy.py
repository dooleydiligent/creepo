from bottle import Bottle, request, response, route, run

import io
import json
import logging
import lxml.etree as ET
import os
import requests
import tempfile
import urllib3

from repository.Proxy import Proxy

app = Bottle()

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

logger.info('registering /pipproxy')

# Proxy all requests to upstreamurl
#proxy = Proxy(__name__, 'https://pypi.org/')
proxy = Proxy(__name__, 'http://localhost:8081/repository/pypi-proxy/')

def before_request(path, url):
  logger.info('before_request({path}, {url})'.format(path=path, url=url))
  return url

def after_request(url, response):
  logger.info('after_request({url}, {status})'.format(url=url, status=response.status))

def callback(input, original_request):
  logger.info('replace embedded hrefs with self-relative links')
  content = input.read()
  parser = ET.XMLParser(recover=True)
  doc = content
  tree  = ET.fromstring(doc, parser=parser)
  if tree:
    for node in tree.findall('.//a[@href]'):
      href = node.get('href')
      if href.find('/packages/') > -1:
        logger.info('href is {href}'.format(href=href))
        package = href.split('/packages/')[1]
        
        logger.info('package is {package}'.format(package=package))
        newhref = '{localhost}/packages/{href}'.format(localhost='http://localhost:5000/pip', href=package)
        logger.info('newhref is {newhref}'.format(newhref=newhref))
        node.set('href', newhref)
    doc = ET.tostring(tree)
    
  with tempfile.NamedTemporaryFile(delete=False) as temp:
    logger.info('tempfile name is {name}'.format(name=temp.name))
    temp.write(doc)
    temp.flush()
  logger.info('wrote tempfile')
  f = open(temp.name, 'rb')
  return f

@app.route('/<path:path>', methods=("GET", "POST"))
def index(path):
    '''Proxy a pip repo request.'''
    logger.info('The request.url is {url}'.format(url=request.url))
    request_path = '{path}'.format(path=path)
    logger.info('request_path is {np}'.format(np=request_path))  

    if request.method == 'POST':
      logger.info('POSTED : {body}'.format(body=request.data))
      parser = ET.XMLParser(recover=True)
      doc = request.data
      tree  = ET.fromstring(doc, parser=parser)
      for node in tree.findall('.//methodName'):
        logger.info('methodName is {methodName}'.format(methodName=node.text))
      
    if request.query_string != '':
      request_path = '{newurl}?{query}'.format(newurl=request_path,query=request.query_string)

    method = request.method
    newrequest = dict()
    newrequest['method'] = request.method
    newrequest['headers'] = request.headers
    newrequest['storage'] = 'pip'
    if not request_path.startswith('packages/'):
      newrequest['path'] = 'simple/{path}'.format(path=request_path)
    else:
      newrequest['path'] = request_path
    newrequest['name'] = '.index.html'
    newrequest['actual_request'] = request
    response = proxy.proxy(newrequest, callback)  

    after_request(path, response)

    # Consider replacing resp.headers
    return response