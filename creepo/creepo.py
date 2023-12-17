import cherrypy


class Creepo(object):
  @cherrypy.expose
  def hello(self):
      return "Hello, World!"

