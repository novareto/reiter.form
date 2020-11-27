import pytest
import roughrider.routing.node
import roughrider.routing.route
import horseman.meta
import horseman.http
import horseman.response
import http
import autoroutes
import webtest


class MockOverhead(horseman.meta.Overhead):

    def __init__(self, node, environ, **params):
        self.node = node
        self.environ = environ
        self.params = params
        self.data = {}

    def set_data(self, data):
        self.data.update(data)


class MockRoutingNode(roughrider.routing.node.RoutingNode):

    request_factory = MockOverhead

    def __init__(self):
        self.routes = autoroutes.Routes()


def fake_route(request):
    return horseman.response.Response.create(200, body=b'OK !')


def failing_route(request):
    raise RuntimeError('Oh, I failed !')


class TestRoutingNode:

    def setup_method(self, method):
        self.node = MockRoutingNode()
        self.node.route('/getter', methods=['GET'])(fake_route)
        self.node.route('/poster', methods=['POST'])(fake_route)

    def test_resolve(self):
        environ = {'REQUEST_METHOD': 'GET'}
        result = self.node.resolve('/getter', environ)
        assert isinstance(result, horseman.response.Response)

        with pytest.raises(horseman.http.HTTPError) as exc:
            self.node.resolve('/getter', {'REQUEST_METHOD': 'POST'})

        # METHOD UNALLOWED.
        assert exc.value.status == http.HTTPStatus(405)

    def test_wsgi_roundtrip(self):
        app = webtest.TestApp(self.node)

        response = app.get('/', status=404)
        assert response.body == b'Nothing matches the given URI'

        response = app.get('/getter')
        assert response.body == b'OK !'

        response = app.post('/getter', status=405)
        assert response.body == (
            b'Specified method is invalid for this resource')
