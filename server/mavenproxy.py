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
import requests

from auth import login_required
from db import get_db

from repository.Proxy import Proxy

bp = Blueprint('mavenproxy', __name__, url_prefix='/m2')
print('registering {proxy}'.format(proxy=bp.url_prefix))

# Proxy all requests to upstreamurl
#maven = Proxy(__name__, 'https://repo.maven.apache.org/maven2')
maven = Proxy(__name__, 'http://localhost:8081/repository/PUBLIC/')

def callback(input):
  return input

@bp.route('/<path:path>')
def index(path):
    '''Proxy a maven request.'''

    newpath = '{path}'.format(path=path)
    if request.query_string != '':
      newpath = '{newurl}?{query}'.format(newurl=newpath,query=request.query_string)

    method = request.method
    newrequest = dict()
    newrequest['method'] = request.method
    newrequest['path'] = newpath
    newrequest['headers'] = request.headers
    newrequest['storage'] = 'maven'
    r = maven.proxy(newrequest)

    resp = make_response(callback(r))
    # Consider replacing resp.headers
    return resp