"""
A Creepo test suite
"""
import os
import sys

import cherrypy
from cherrypy.test import helper


sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))

import creepo.rest # pylint: disable=wrong-import-position


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
