from bottle import BaseResponse, Bottle, request, route, run

import lxml.etree as ET

import requests
import tempfile
from Proxy import Proxy

app = Bottle()

def callback(input, original_request):
  # TODO: Have the caller suggest the local file path
  print('callback: save the response to a local file')
  content = input.read()

  with tempfile.NamedTemporaryFile(delete=False) as temp:
    print('tempfile name is {name}'.format(name=temp.name))
    temp.write(content)
    temp.flush()
    
    ## TODO: Make relative links self-relative
    
  print('wrote tempfile')
  f = open(temp.name, 'rb')
  return f
  
@app.route('/<path:path>')
def index(path):
    '''Proxy an arbitrary request.
    The route is http://localhost:5000/proxy/protocol/host/path
    Where path is [protocol/host/path]
    '''
    # Looks like protocol/hostname/path
    print('ORIGINAL REQUEST: {path}'.format(path=path))
    splitpath = path.split('/', 3)
    protocol = splitpath.pop(0)
    host = splitpath.pop(0)
    path = '/'.join(splitpath)

    headers = {k: v for k, v in request.headers.items()}
    headers['Host'] = '{host}'.format(host=host)

    remote = '{protocol}://{host}/'.format(protocol=protocol, host=host)
    
    newurl = '{protocol}://{host}/{path}'.format(protocol=protocol, host=host, path=path)
    if request.query_string != '':
      newurl = '{newurl}?{query}'.format(newurl=newurl,query=request.query_string)

    print ('Getting {newurl}'.format(newurl=newurl))

    newrequest = dict()
    newrequest['method'] = request.method
    newrequest['headers'] = request.headers
    newrequest['storage'] = 'pip'
    newrequest['path'] = path
    newrequest['name'] = '.index.html'
    newrequest['actual_request'] = request
    
    print('Proxying TYPE: {type} {remote}'.format(type=__name__, remote=remote))

    p = Proxy(__name__, remote)
    resp = p.proxy(newrequest, callback)

    print('header content-type={ct}'.format(ct=resp.headers['content-type']))
    if resp.headers['content-type'].lower().startswith('text/'):
      # Make the xhtml response point back to this host
      # TODO: make this better
      parser = ET.XMLParser(recover=True)
      doc = resp.body
      try:
        tree  = ET.fromstring(doc, parser=parser)
        if tree:
          for node in tree.findall('.//*[@src]'):
            original = node.get('src')
            save_original = original
            if original.startswith('#'):
                original = '/{original}'.format(original=original)
            if original.startswith('/'):
                original = '{protocol}://{host}{original}'.format(protocol=protocol,host=host,original=original)
            original = original.replace('://', '/')
            original = 'http://localhost:5000/proxy/{original}'.format(protocol=protocol,host=host,original=original)
            print('changed @src from {save_original} to {original}'.format(save_original=save_original, original=original))
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
                node.text = ''# print('registering {proxy}'.format(proxy=bp.url_prefix))

          resp = BaseResponse(body=ET.tostring(tree), status='200 OK')
          # resp = make_response(ET.tostring(tree))
        else:
          print('TODO: Send the proper mime type')
          print('ORIGINAL RESPONSE HEADERS ARE {headers}'.format(resp.headers))
          resp = BaseResponse(body=resp.body, status=resp.status, headers={'content-type': contentType})
      except:
          print('TODO 2: Send the proper mime type')
          print('ORIGINAL RESPONSE HEADERS ARE {headers}'.format(resp.headers))
          resp = BaseResponse(body=resp.body, status=resp.status, headers={'content-type': contentType})
        
    else:
      resp = BaseResponse(body=resp.body, status=resp.status)

    headers = {}
    for k, v in resp.headers.items():
      headers[k] = v
    return resp
