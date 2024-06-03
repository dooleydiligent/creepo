"""Unit tests for Npm Proxy"""

import os
import sys
import unittest
import tempfile
from unittest.mock import patch

from urllib3._collections import HTTPHeaderDict

from mocks import MockedLogger, MockedPoolManager

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../creepo"))
)

from npmproxy import NpmProxy  # pylint: disable=wrong-import-position


class TestNpmProxy(unittest.TestCase):
    """Unit tests for npmproxy"""

    def test_npm(self):
        """Test npm proxy"""

        def start_ok_response(status, headers):  # pylint: disable=unused-argument
            self.assertEqual(status, "200 OK")

        content = b'{"versions": []}'
        request = {
            "REQUEST_URI": "/m2/org/apache/maven/plugins/maven-clean-plugin/2.5/maven-clean-plugin-2.5.pom",
            "log": [],
        }

        config = {
            "log": [],
        }

        config["logger"] = MockedLogger(request["log"])

        with patch("urllib3.PoolManager") as mock_poolmanager:

            with tempfile.TemporaryDirectory() as tmpdirname:
                with unittest.mock.patch.dict("os.environ", {"HOME": tmpdirname}):

                    mock_poolmanager.return_value = MockedPoolManager(
                        status_code=200,
                        response_headers=HTTPHeaderDict(
                            {"Content-Type": "application/json"}
                        ),
                        content=content,
                    )

                    proxy = NpmProxy(config)

                    result = list(proxy.proxy(request, start_ok_response))
                    print(f"  Actual  type: {type(result)}: value: {result}")
                    print(
                        f"Leave this in place to capture MockedLogger output\n{request}"
                    )

                    self.assertEqual(content, result[0], "Expected the mocked response")
