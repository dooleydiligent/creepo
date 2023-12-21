import unittest
import unittest.mock
import tempfile

from creepo.proxy import Proxy


class TestProxy(unittest.TestCase):
    def test_type(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            with unittest.mock.patch.dict('os.environ', {'HOME': tmpdirname}):
                proxy = Proxy("test", 'https://some.random.url/path')
                self.assertEqual(proxy.type, "test",
                                 "Expected type to be 'test'")
                self.assertEqual(proxy.filename, "",
                                 "Expected filename to be empty")
                self.assertEqual(proxy.base, '{tmpdirname}/.CREEPO_BASE'.format(tmpdirname=tmpdirname),
                                 "Expected _creepo to be set to {tmpdirname} but it is {other}".format(
                    tmpdirname=tmpdirname, other=proxy.base))
            with unittest.mock.patch.dict('os.environ', {'CREEPO_BASE': tmpdirname}):
                proxy = Proxy("test", 'https://some.random.url/path')
                self.assertEqual(proxy.base, '{tmpdirname}'.format(tmpdirname=tmpdirname), "Expected _creepo to be set to {tmpdirname} but it is {other}".format(
                    tmpdirname=tmpdirname, other=proxy.base))
                def callback(self, input, outpath):
                  print('callback')
                