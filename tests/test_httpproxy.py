"""Unit tests for Proxy while mocking cherrypy """
import unittest
import tempfile

from unittest.mock import patch

from creepo.httpproxy import Proxy  # pylint: disable=import-outside-toplevel


class MockedLogger:  # pylint: disable=missing-class-docstring, missing-function-docstring, unused-argument
    def __init__(self, log):
        self.log = log

    def info(self, *args):
        print(args)
        for arg in args:
            self.log.append(arg)

    def debug(self, *args):
        print(args)
        for arg in args:
            self.log.append(arg)

    def warning(self, *args):
        print(args)
        for arg in args:
            self.log.append(arg)


class MockedPoolManager:  # pylint: disable=missing-class-docstring, missing-function-docstring, unused-argument

    class Response:
        @property
        def status(self):
            return 200

        @property
        def headers(self):
            return {}

        @property
        def data(self):
            print("this is mock request")
            return b'It werkz!'

        def release_conn(self):
            print("release_conn")

    def request(self, method, url, decode_content, preload_content, headers) -> Response:
        return self.Response()


class TestHttpProxy(unittest.TestCase):
    """Unit tests for httpproxy module using cherrypy and mocks"""

    def test_persist(self):
        """Test for persist - just testing the cache here"""

        def start_response(status, _headers):
            self.assertEqual(status, '200 OK')

        request = {
            'path': '/proxy/file.name',
            'storage': 'test',
            'content_type': 'text/html',
            'headers': {},
            'method': 'GET',
            'log': []
        }

        request['logger'] = MockedLogger(request['log'])

        with patch('urllib3.PoolManager') as mock_poolmanager:
            mock_poolmanager.return_value = MockedPoolManager()

            with tempfile.TemporaryDirectory() as tmpdirname:
                with unittest.mock.patch.dict('os.environ', {'HOME': tmpdirname}):

                    proxy = Proxy(
                        "test", {'registry': 'https://some.random.url/path:10111'}, {'no_cache': 'False'})

                    result = proxy.proxy(request, start_response)
                    #
                    # Note: Leave both of the next two 'print' statements in place to facilitate debugging
                    #       ATM I speculate that request['response'] does not get populated until the "result"
                    #       generator is listed, e.g. list(result), below
                    print(
                        f"  Actual  type: {type(result)}: value: {list(result)}")
                    print(
                        f"Leave this in place to capture MockedLogger output\n{request}")

        self.assertNotEqual(request.get(
            'response'), None, "Expected a response in the original request")

        self.assertEqual(
            request['response'], b"It werkz!", "Expected the mocked response")
