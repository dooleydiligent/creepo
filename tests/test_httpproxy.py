"""Unit tests for Proxy while mocking cherrypy (and others)"""
import unittest
import tempfile
from unittest.mock import patch

from diskcache import Cache

from mocks import MockedLogger, MockedPoolManager
from creepo.httpproxy import HttpProxy


class TestHttpProxyCache(unittest.TestCase):
    """Unit tests for httpproxy module using cherrypy and mocks"""

    def test_no_cache_false(self):
        """Test for persist - just testing the cache here"""

        def start_ok_response(status, headers):  # pylint: disable=unused-argument
            self.assertEqual(status, '200 OK')

        request = {
            'path': '/proxy/file.name',
            'storage': 'test',
            'content_type': 'text/html',
            'headers': {},
            'method': 'GET',
            'log': []
        }

        content = b"It werx!"
        request['logger'] = MockedLogger(request['log'])

        with patch('urllib3.PoolManager') as mock_poolmanager:

            with tempfile.TemporaryDirectory() as tmpdirname:
                with unittest.mock.patch.dict('os.environ', {'HOME': tmpdirname}):

                    mock_poolmanager.return_value = MockedPoolManager(
                        status_code=200, response_headers={}, content=content)

                    proxy = HttpProxy(
                        {
                            'no_cache': 'False', 'logger': request['logger'],
                            'test':
                            {'registry': 'https://some.random.url/path:10111'}
                        }, 'test')

                    result = proxy.rest_proxy(
                        request, start_ok_response)
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
                        request['response'], content, "Expected the mocked response")

                    with Cache(proxy.base) as cache:
                        testdata = cache.get(request['output_filename'])
                        self.assertNotEqual(
                            testdata, None, 'Expect to cache the response but it was not found')
                        self.assertEqual(
                            testdata, content, "Expected the actual response to have been cached but found something else")

                    # Subsequent requests work slightly differently
                    result = proxy.rest_proxy(request, start_ok_response)

    def test_no_cache_true(self):
        """Test persistence"""

        def start_response(status, headers):  # pylint: disable=unused-argument
            self.assertEqual(status, '200 OK')

        request = {
            'path': '/proxy/file.name',
            'storage': 'test',
            'content_type': 'text/html',
            'headers': {},
            'method': 'GET',
            'log': []
        }

        content = b"It werx!"

        request['logger'] = MockedLogger(request['log'])

        with patch('urllib3.PoolManager') as mock_poolmanager:

            with tempfile.TemporaryDirectory() as tmpdirname:
                with unittest.mock.patch.dict('os.environ', {'HOME': tmpdirname}):

                    mock_poolmanager.return_value = MockedPoolManager(
                        status_code=200, response_headers={}, content=content)

                    proxy = HttpProxy(
                        {
                            'logger': request['logger'],
                            'test':
                            {'registry': 'https://some.random.url/path:10111'}
                        }, 'test')

                    result = proxy.rest_proxy(request, start_response)
                    #
                    # Note: Leave both of the next two 'print' statements in place to facilitate debugging
                    #       ATM I speculate that request['response'] does not get populated until the "result"
                    #       generator is listed, e.g. list(result), below
                    print(
                        f"  Actual  type: {type(result)}: value: {list(result)}")
                    print(
                        f"Leave this in place to capture MockedLogger output\n{request}")

                self.assertNotEqual(request.get(
                    'response'), None, "Expected the response in the original request")

                self.assertEqual(
                    request.get('response'), content, "Expected the mocked response")

                with Cache(proxy.base) as cache:
                    testdata = cache.get(request['output_filename'])
                    self.assertEqual(
                        testdata, None, 'Expect NOT to cache the response but it was found instead')
