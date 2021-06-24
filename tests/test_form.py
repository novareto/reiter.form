import pytest
from reiter.form.meta import Trigger
from reiter.form.form import FormView


class TestFormView:

    def test_baseclass(self, environ, request_class):
        assert FormView.triggers == {}
        request = request_class(environ)
        form = FormView(request)
        assert form.namespace() == {
            'actions': {},
            'request': request,
            'view': form
        }
        with pytest.raises(LookupError):
            form.process_action('test')

    def test_form_class(self, environ, request_class):

        class Form(FormView):

            def POST(self):
                return self.process_action(self.params['action'])

            @Trigger.trigger(title='Title')
            def do_something(self, request, data):
                return 'I did something'

        assert Form.triggers == {
            'trigger.do_something': Trigger(
                id='trigger.do_something',
                title='Title',
                method=Form.do_something,
                css='',
                order=10,
                condition=None
            )
        }
        request = request_class(environ)
        form = Form(request, action='trigger.do_something')
        assert form.namespace() == {
            'actions': {
                'trigger.do_something': Trigger(
                    id='trigger.do_something',
                    title='Title',
                    method=Form.do_something,
                    css='',
                    order=10,
                    condition=None
                )
            },
            'request': request,
            'view': form
        }
        with pytest.raises(LookupError):
            form.process_action('test')

        assert form.POST() == 'I did something'
