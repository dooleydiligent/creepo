"""Unit tests for proxy"""
import unittest
import unittest.mock
import tempfile

from creepo.httpproxy import Proxy


class TestProxy(unittest.TestCase):
    """Unit tests for Proxy"""

    def test_type(self):
        """Test for type"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            with unittest.mock.patch.dict('os.environ', {'HOME': tmpdirname}):
                proxy = Proxy(
                    "test", {'registry': 'https://some.random.url/path'}, {})
                self.assertEqual(proxy.type, "test",
                                 "Expected type to be 'test'")
                self.assertEqual(proxy.base, f"{tmpdirname}/.CREEPO_BASE",
                                 f"Expected _creepo to be set to {tmpdirname} but it is {proxy.base}")
            with unittest.mock.patch.dict('os.environ', {'CREEPO_BASE': tmpdirname}):
                proxy = Proxy(
                    "test", {'registry': 'https://some.random.url/path'}, {})
                self.assertEqual(
                    proxy.base, f"{tmpdirname}", f"Expected _creepo to be set to {tmpdirname} but it is {proxy.base}")

    def test_mimetype(self):
        """Test for mimetype"""
        proxy = Proxy("test", {'registry': 'https://some.random.url/path'}, {})
        self.assertEqual(proxy.mimetype("index.html", "application/octet-stream"), "text/html",
                         "Expected mime type default to be text/html")
        self.assertEqual(proxy.mimetype("", "application/octet-stream"), "application/octet-stream",
                         "Expected mime type default to be text/html")
