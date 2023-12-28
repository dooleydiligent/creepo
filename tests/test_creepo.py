"""
A Creepo test suite
"""
import cherrypy
from cherrypy.test import helper
import creepo.rest


class SimpleCherryPyTest(helper.CPWebCase):
    """
    An entry point into the test suite
    """
    @staticmethod
    def setup_server():
        """
        Setup the server
        """
        cherrypy.tree.mount(creepo.rest.Creepo(), '/', {})

    def test_hello(self):
        """
        Test the hello endpoint
        """
        self.getPage("/hello")
        self.assertStatus('200 OK')

    def test_generate_does_not_exist(self):
        """
        Prove (more or less) that this is the server we think we are testing
        """
        self.getPage("/generate")
        self.assertStatus('404 Not Found')
