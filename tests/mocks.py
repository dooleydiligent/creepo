"""Some mocks for testing"""
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
    def __init__(self, status_code, response_headers, content):
        self.status_code = status_code
        self.response_headers = response_headers
        self.content = content

    class Response:
        @property
        def status(self):
            return self.status_code

        @status.setter
        def status(self, status_code):
            self.status_code = status_code

        @property
        def headers(self):
            return self.response_headers

        @headers.setter
        def headers(self, response_headers):
            self.response_headers = response_headers

        @property
        def data(self):
            return self.content

        @data.setter
        def data(self, content):
            self.content = content

        def release_conn(self):
            print("release_conn")

    def request(self, method, url, decode_content, preload_content, headers) -> Response:
        response = self.Response()
        response.status = self.status_code
        response.headers = self.response_headers
        response.data = self.content
        return response
