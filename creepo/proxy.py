from flask import Blueprint
from flask import flash
from flask import g
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

import lxml.etree as ET
# import xml.etree.ElementTree as ET

import requests

from creepo.auth import login_required
from creepo.db import get_db

bp = Blueprint('proxy', __name__, url_prefix='/proxy')

@bp.route('/<path:path>')
def index(path):
    '''Proxy an arbitrary request.'''

    splitpath = path.split('/', 3)
    protocol = splitpath.pop(0)
    host = splitpath.pop(0)
    path = '/'.join(splitpath)
    print 'PATH: {path} ? QUERY: {query}'.format(path=path,query=request.query_string)
    print '[{protocol}]/[{host}]/[{path}]'.format(protocol=protocol,host=host,path=path)

    if (request.query_string != ''):
      print('trying to get {protocol}://{host}/{path}?{query}'.format(protocol=protocol, host=host, path=path, query=request.query_string))
    else:
      print('trying to get {protocol}://{host}/{path}'.format(protocol=protocol, host=host, path=path))

    headers = {k: v for k, v in request.headers.items()}
    headers['Host'] = '{host}'.format(host=host)
    newurl = '{protocol}://{host}/{path}'.format(protocol=protocol, host=host, path=path)
    if request.query_string != '':
      newurl = '{newurl}?{query}'.format(newurl=newurl,query=request.query_string)

    print 'Getting {newurl}'.format(newurl=newurl)

    r = requests.get(newurl, headers=headers)

    print 'Content-Type: ', r.headers['content-type']

    resp = make_response('temp')

    if r.headers['content-type'].lower().startswith('text/html'):
      parser = ET.XMLParser(recover=True)

      doc = r.text
      tree  = ET.fromstring(doc, parser=parser)

      for node in tree.findall('.//*[@src]'):
        original = node.get('src')
        if original.startswith('#'):
            original = '/{original}'.format(original=original)
        if original.startswith('/'):
            original = '{protocol}://{host}{original}'.format(protocol=protocol,host=host,original=original)
        original = original.replace('://', '/')
        original = 'http://localhost:5000/proxy/{original}'.format(protocol=protocol,host=host,original=original)
        node.set('src', original)

      for node in tree.findall('.//*[@href]'):
        original = node.get('href')
        if original.startswith('#'):
          original = '/{original}'.format(original=original)
        if original.startswith('/'):
          original = '{protocol}://{host}{original}'.format(protocol=protocol,host=host,original=original)
        original = original.replace('://', '/')
        original = 'http://localhost:5000/proxy/{original}'.format(protocol=protocol,host=host,original=original)
        node.set('href', original)

      for node in tree.iter():
        if node.tag != 'link' and node.tag != 'video' and node.tag != 'source':
          if node.text is None:
            node.text = ''

      resp = make_response(ET.tostring(tree))
    else:
      resp = make_response(r.content)

    headers = {}
    for k, v in request.headers.items():
      print('Headers: {k} = {v}'.format(k=k,v=v))
      headers[k] = v
    resp.headers = headers
    return resp