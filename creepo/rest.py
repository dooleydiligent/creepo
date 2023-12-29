"""The creepo class"""
import cherrypy


class Creepo:  # pylint: disable=too-few-public-methods
    """The Creepo class"""
    @cherrypy.expose
    def hello(self):
        """A simple hello method"""
        return "Hello, World!"
