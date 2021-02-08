import collections
import inspect
import typing
from dataclasses import dataclass
from horseman.meta import Overhead


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
    def trigger(cls, id, title, css="", order=10, condition=None):
        def mark_as_trigger(func):
            func.trigger = cls(
                id=f'trigger.{id}',
                title=title,
                css=css,
                method=func,
                order=order,
                condition=condition
            )
            return func
        return mark_as_trigger

    @staticmethod
    def triggers(cls):
        for name, func in inspect.getmembers(cls, predicate=(
                lambda x: inspect.isfunction(x) and hasattr(x, 'trigger'))):
            yield func.trigger.id, func.trigger


class FormViewMeta(type):

    def __init__(cls, name, bases, attrs):
        type.__init__(cls, name, bases, attrs)
        cls.triggers = None

    def __call__(cls, *args, **kwargs):
        if cls.triggers is None:
            triggers = list(Trigger.triggers(cls))
            triggers.sort(key=lambda trigger: trigger[1].order)
            cls.triggers = collections.OrderedDict(triggers)

        return type.__call__(cls, *args, **kwargs)
