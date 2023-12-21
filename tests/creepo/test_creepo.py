import cherrypy
from cherrypy.test import helper
import creepo.creepo

class SimpleCPTest(helper.CPWebCase):
    @staticmethod
    def setup_server():
        cherrypy.tree.mount(creepo.creepo.Creepo(), '/', {})
    def test_hello(self):
        self.getPage("/hello")
        self.assertStatus('200 OK')
    def test_generate_does_not_exist(self):
        self.getPage("/generate")
        self.assertStatus('404 Not Found')
