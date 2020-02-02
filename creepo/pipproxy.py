from bottle import Bottle, request, response, route, run

import io
import json
import lxml.etree as ET
import os
import requests
import tempfile
import urllib3

from repository.Logger import Logger
from repository.Proxy import Proxy

logger = Logger(__name__)
logger.debug('registering {name}'.format(name=__name__))
app = Bottle()
proxy = Proxy(__name__, 'http://localhost:8081/repository/pypi-proxy/')

def before_request(path, url):
  logger.info('before_request({path}, {url})'.format(path=path, url=url))
  return url

def after_request(url, status):
  logger.info('after_request({url}, {status})'.format(url=url, status=status))

def callback(input, return_path):
  content = input.read()
  input.close()
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
    
  outfile = open(return_path, 'wb')
  outfile.write(doc)
  outfile.close()
  logger.debug('wrote {file}'.format(file=return_path))
  return return_path

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
    resp = proxy.proxy(newrequest, callback)  
    content = None
    status = 404
    if resp:
      if os.path.exists(resp):
        status = 200
      if os.path.isdir(resp):
        resp = os.path.join(resp, '...')

      outfile = open(resp, 'rb')
      content = outfile.read()
      outfile.close()

    after_request(request_path, status)
    return content
