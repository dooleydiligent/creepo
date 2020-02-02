import os

from bottle import Bottle, route, run
from creepo.repository.Logger import Logger

logger = Logger('CREEPO')

app = Bottle()

@app.route("/hello")
def hello():
  logger.debug('Hello World!')
  return "Hello, World!"

def create_app(test_config=None):
  """Create and configure an instance of the Flask application."""

  import creepo.mavenproxy, creepo.npmproxy, creepo.pipproxy
#  import blog, mavenproxy, npmproxy, pipproxy, proxy
#  app.mount('/blog', blog.app)
#  app.mount('/proxy', proxy.app)
  app.mount('/npm', npmproxy.app)
  app.mount('/m2', mavenproxy.app)
  app.mount('/pip', pipproxy.app)
  return app

if __name__ == '__main__':
  logger.debug('my name is {name}'.format(name=__name__))
  app = create_app()

#  application = bottle.default_app()
#  from paste import httpserver
#  httpserver.serve(application, host='0.0.0.0', port=5000, debug=True)

  run(app, server='paste', host='localhost', port=5000, debug=True)

# __all__ = ["app"]
