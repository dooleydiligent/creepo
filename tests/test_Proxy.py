"""Unit tests for proxy"""
import unittest

import tempfile

from creepo.httpproxy import Proxy


class TestProxy(unittest.TestCase):
    """Unit tests for Proxy"""

    def test_kind(self):
        """Test for type"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            with unittest.mock.patch.dict('os.environ', {'HOME': tmpdirname}):
                proxy = Proxy(
                    "test", {'registry': 'https://some.random.url/path'}, {})
                self.assertEqual(proxy.kind, "test",
                                 "Expected kind to be 'test'")
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

    def test_no_cache(self):
        """Test for no_cache"""
        proxy = Proxy("test", {
                      'registry': 'https://some.random.url/path'}, {'no_cache': 'anything-but-false'})
        self.assertEqual(proxy.no_cache, True,
                         "Expected no_cache to default True")
        proxy = Proxy("test", {
                      'registry': 'https://some.random.url/path'}, {'no_cache': 'False'})
        self.assertEqual(proxy.no_cache, False,
                         "Expected no_cache to default False when specified")
