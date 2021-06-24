import pytest
from typing import Optional
from io import BytesIO
from frozendict import frozendict
from horseman.meta import Overhead
from horseman.http import Query
from horseman.parsers import Data


@pytest.fixture(scope="session")
def environ():
    return frozendict({
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'SERVER_NAME': 'test_domain.com',
        'SERVER_PORT': '80',
        'HTTP_HOST': 'test_domain.com:80',
        'SERVER_PROTOCOL': 'HTTP/1.0',
        'wsgi.url_scheme': 'http',
        'wsgi.version': (1,0),
        'wsgi.run_once': 0,
        'wsgi.multithread': 0,
        'wsgi.multiprocess': 0,
        'wsgi.input': BytesIO(b""),
        'wsgi.errors': BytesIO()
    })


class Request(Overhead):

    __slots__ = ('_data', 'environ', 'script_name', 'method', 'query')

    def __init__(self, environ):
        self.environ = environ
        self.script_name = environ['SCRIPT_NAME']
        self.method = environ['REQUEST_METHOD'].upper()
        self.query = Query.from_environ(environ)
        self._data = None

    def set_data(self, data: Data):
        self._data = data

    def get_data(self) -> Optional[Data]:
        return self._data


@pytest.fixture(scope="session")
def request_class():
    return Request
