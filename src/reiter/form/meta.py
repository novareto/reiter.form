import collections
import inspect
import typing
from dataclasses import dataclass


Condition = typing.Callable[..., bool]


@dataclass
class Trigger:
    id: str
    title: str
    method: typing.Callable
    css: str
    order: int
    condition: Condition = None

    def __call__(self, *args, **kwargs):
        return self.method(*args, **kwargs)

    @classmethod
    def trigger(cls, title, name=None, css="", order=10, condition=None):
        def mark_as_trigger(func):
            func.trigger = cls(
                id=f'trigger.{name or func.__name__}',
                title=title,
                css=css,
                method=func,
                order=order,
                condition=condition
            )
            return func
        return mark_as_trigger

    @staticmethod
    def triggers(cls: typing.Type):
        for name, func in inspect.getmembers(cls, predicate=(
                lambda x: inspect.isfunction(x) and hasattr(x, 'trigger'))):
            yield func.trigger


class Triggers(collections.OrderedDict):

    def __setitem__(self, name, value):
        assert isinstance(name, str)
        assert isinstance(value, Trigger)
        super().__setitem__(name, value)

    def filtered(self, *args, **kwargs):
        for name, trigger in self.items():
            if trigger.condition and not trigger.condition(*args, **kwargs):
                continue
            yield name, trigger


class TriggersScope(type):

    def __new__(cls, name, bases, attrs):
        if not 'triggers' in attrs:
            triggers = []
            for base in bases:
                triggers.extend(list(Trigger.triggers(base)))

            for attr, value in attrs.items():
                if inspect.isfunction(value) and hasattr(value, 'trigger'):
                    triggers.append(value.trigger)
            triggers.sort(key=lambda trigger: trigger.order)
            attrs['triggers'] = Triggers(
                ((trigger.id, trigger) for trigger in triggers)
            )
        return type.__new__(cls, name, bases, attrs)
