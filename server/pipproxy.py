
from flask import Blueprint
from flask import flash
from flask import g
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort
from werkzeug.wrappers import Response
import io
import json
import lxml.etree as ET
import os
import requests
import tempfile
import urllib3
# from suds.client import Client
# client = Client("https://wsvc.cdiscount.com/MarketplaceAPIService.svc?wsdl")

from auth import login_required
from db import get_db

from file_like import IOInterface
from repository.Proxy import Proxy

bp = Blueprint('pipproxy', __name__, url_prefix='/pip/pip/pip')
print('registering {proxy}'.format(proxy=bp.url_prefix))

# Proxy all requests to upstreamurl
#proxy = Proxy(__name__, 'https://pypi.org/')
proxy = Proxy(__name__, 'http://localhost:8081/repository/pypi-proxy/')

def before_request(path, url):
  print('before_request({path}, {url})'.format(path=path, url=url))
  return url

def after_request(url, response):
  print('after_request({url}, {status})'.format(url=url, status=response.status))

def callback(input):
  print('replace embedded hrefs with self-relative links')
  content = input.read()
  parser = ET.XMLParser(recover=True)
  doc = content
  tree  = ET.fromstring(doc, parser=parser)
  for node in tree.findall('.//a[@href]'):
    href = node.get('href')
    print('href is {href}'.format(href=href))
    package = href.split('/packages/')[1]
    print('package is {package}'.format(package=package))
    newhref = '{localhost}{prefix}/packages/{href}'.format(localhost='http://localhost:5000', prefix=bp.url_prefix, href=package)
    print('newhref is {newhref}'.format(newhref=newhref))
    node.set('href', newhref)

  with tempfile.NamedTemporaryFile(delete=False) as temp:
    print('tempfile name is {name}'.format(name=temp.name))
    temp.write(ET.tostring(tree))
    temp.flush()
  print('wrote tempfile')
  f = open(temp.name, 'rb')
  return f

@bp.route('/<path:path>', methods=("GET", "POST"))
def index(path):
    '''Proxy a pip repo request.'''
    print('The request.url is {url}'.format(url=request.url))
    request_path = '{path}'.format(path=path)
    print('request_path is {np}'.format(np=request_path))  

    if request.method == 'POST':
      print('POSTED : {body}'.format(body=request.data))
      parser = ET.XMLParser(recover=True)
      doc = request.data
      tree  = ET.fromstring(doc, parser=parser)
      for node in tree.findall('.//methodName'):
        print('methodName is {methodName}'.format(methodName=node.text))
      
    if request.query_string != '':
      request_path = '{newurl}?{query}'.format(newurl=request_path,query=request.query_string)

    method = request.method
    newrequest = dict()
    newrequest['method'] = request.method
    newrequest['headers'] = request.headers
    newrequest['storage'] = 'pip'
    newrequest['path'] = request_path
    newrequest['name'] = '.index.html'
    response = proxy.proxy(newrequest, callback)  

    after_request(path, response)

    # Consider replacing resp.headers
    return response