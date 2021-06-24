from reiter.form.meta import Trigger, TriggersScope


class TestTrigger:

    def test_decorator(self):

        @Trigger.trigger(title='Title')
        def do_something(item):
            return 'I did something'

        assert do_something.trigger == Trigger(
            id='trigger.do_something',
            title='Title',
            method=do_something,
            css='',
            order=10
        )

    def test_decorator_class_scope(self):

        class Scope:
            @Trigger.trigger(title='Title')
            def do_something(item):
                return 'I did something'

        assert Scope.do_something.trigger == Trigger(
            id='trigger.do_something',
            title='Title',
            method=Scope.do_something,
            css='',
            order=10
        )

        assert list(Trigger.triggers(Scope)) == [
            Scope.do_something.trigger
        ]

    def test_decorator_class_scope_multiple(self):

        class Scope:

            @Trigger.trigger(title='Title')
            def do_something(item):
                return 'I did something'

            @Trigger.trigger(title='Title')
            def something_else(item):
                return 'I did something else'

        assert list(Trigger.triggers(Scope)) == [
            Scope.do_something.trigger,
            Scope.something_else.trigger,
        ]

    def test_decorator_class_scope_inheritance(self):

        class Scope:

            @Trigger.trigger(title='Title')
            def do_something(item):
                return 'I did something'

        class Scope2(Scope):
            @Trigger.trigger(title='Title')
            def something_else(item):
                return 'I did something else'

        assert list(Trigger.triggers(Scope)) == [
            Scope.do_something.trigger,
        ]

        assert list(Trigger.triggers(Scope2)) == [
            Scope.do_something.trigger,
            Scope2.something_else.trigger,
        ]

    def test_decorator_class_scope_inheritance_override(self):

        class Scope:

            @Trigger.trigger(title='Title')
            def do_something(item):
                return 'I did something'

        class Scope2(Scope):
            @Trigger.trigger(title='Title')
            def do_something(item):
                return 'I did something else'

        assert list(Trigger.triggers(Scope)) == [
            Scope.do_something.trigger,
        ]

        assert list(Trigger.triggers(Scope2)) == [
            Scope2.do_something.trigger,
        ]

        assert Scope.do_something.trigger != Scope2.do_something.trigger

    def test_no_condition(self):

        def do_something():
            return 'I did something'

        trigger = Trigger(
            id='some action',
            title='My Action Title',
            method=do_something,
            css='',
            order=1
        )

        assert trigger.id == 'some action'
        assert trigger.title == 'My Action Title'
        assert trigger.method is do_something
        assert trigger.css == ''
        assert trigger.order == 1
        assert trigger.condition is None
        assert trigger() == 'I did something'

    def test_condition(self):

        def do_something(item):
            return 'I did something'

        def only_document(item):
            return item.type == 'document'

        trigger = Trigger(
            id='some action',
            title='My Action Title',
            method=do_something,
            condition=only_document,
            css='',
            order=1,
        )

        assert trigger.id == 'some action'
        assert trigger.title == 'My Action Title'
        assert trigger.method is do_something
        assert trigger.css == ''
        assert trigger.order == 1
        assert trigger.condition is  only_document
        assert trigger(object()) == 'I did something'


class TestTriggerScope:

    def test_empty(self):

        class Empty(metaclass=TriggersScope):
            pass

        assert Empty.triggers == {}

    def test_empty_inheritance(self):

        class Empty(metaclass=TriggersScope):
            pass

        class AnotherEmpty(Empty):
            pass

        assert Empty.triggers == {}
        assert AnotherEmpty.triggers == {}
        assert Empty.triggers is not AnotherEmpty.triggers

    def test_trigger(self):

        class OneTrigger(metaclass=TriggersScope):

            @Trigger.trigger(title='Title')
            def do_something(item):
                return 'I did something else'

        assert OneTrigger.triggers == {
            'trigger.do_something': Trigger(
                id='trigger.do_something',
                title='Title',
                method=OneTrigger.do_something,
                css='',
                order=10,
                condition=None
            )
        }

    def test_multiple_triggers(self):

        class Triggers(metaclass=TriggersScope):

            @Trigger.trigger(title='Title', order=50)
            def do_something(item):
                return 'I did something else'

            @Trigger.trigger(title='Title')
            def do_something_else(item):
                return 'I did something else'

        obj = Triggers()
        assert obj.triggers == {
            'trigger.do_something_else': Trigger(
                id='trigger.do_something_else',
                title='Title',
                method=Triggers.do_something_else,
                css='',
                order=10,
                condition=None
            ),
            'trigger.do_something': Trigger(
                id='trigger.do_something',
                title='Title',
                method=Triggers.do_something,
                css='',
                order=50,
                condition=None
            )
        }

    def test_triggers_inheritance(self):

        class Base(metaclass=TriggersScope):

            @Trigger.trigger(title='Title')
            def do_something(item):
                return 'I did something'

        class Edit(Base):

            @Trigger.trigger(title='Title')
            def do_something_else(item):
                return 'I did something else'

        assert Base.triggers == {
            'trigger.do_something': Trigger(
                id='trigger.do_something',
                title='Title',
                method=Base.do_something,
                css='',
                order=10,
                condition=None
            )
        }
        assert Edit.triggers == {
            'trigger.do_something_else': Trigger(
                id='trigger.do_something_else',
                title='Title',
                method=Edit.do_something_else,
                css='',
                order=10,
                condition=None
            ),
            'trigger.do_something': Trigger(
                id='trigger.do_something',
                title='Title',
                method=Base.do_something,
                css='',
                order=10,
                condition=None
            ),
        }

    def test_triggers_inheritance_override(self):

        class Base(metaclass=TriggersScope):

            @Trigger.trigger(title='Title')
            def do_something(item):
                return 'I did something'

        class Edit(Base):

            @Trigger.trigger(title='Title')
            def do_something(item):
                return 'I did something else'

        assert Edit.triggers == {
            'trigger.do_something': Trigger(
                id='trigger.do_something',
                title='Title',
                method=Edit.do_something,
                css='',
                order=10,
                condition=None
            )
        }

    def test_triggers_direct_override(self):

        class Base(metaclass=TriggersScope):

            triggers = 'Some value'

            @Trigger.trigger(title='Title')
            def do_something(item):
                return 'I did something'

        assert Base.triggers == 'Some value'
        assert list(Trigger.triggers(Base)) == [
            Base.do_something.trigger,
        ]
