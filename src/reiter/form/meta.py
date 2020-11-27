import collections
import inspect
import typing
import pydantic
import wtforms
from dataclasses import dataclass
from horseman.meta import APIView
from wtforms_pydantic.converter import Converter, model_fields


@dataclass
class Trigger:
    id: str
    title: str
    method: typing.Callable
    css: str
    order: int

    def __call__(self, *args, **kwargs):
        return self.method(*args, **kwargs)

    @classmethod
    def trigger(cls, id, title, css="btn btn-primary", order=10):
        def mark_as_trigger(func):
            func.trigger = cls(
                id=f'trigger.{id}',
                title=title,
                css=css,
                method=func,
                order=order
            )
            return func
        return mark_as_trigger

    @staticmethod
    def triggers(cls):
        for name, func in inspect.getmembers(cls, predicate=(
                lambda x: inspect.isfunction(x) and hasattr(x, 'trigger'))):
            yield name, func.trigger


trigger = Trigger.trigger


class Form(wtforms.form.BaseForm):

    @classmethod
    def from_model(cls, model: pydantic.BaseModel,
                   only=(), exclude=(), **overrides):
        return cls(Converter.convert(
            model_fields(model, only=only, exclude=exclude), **overrides
        ))


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


class FormView(APIView, metaclass=FormViewMeta):

    title: str = ""
    description: str = ""
    action: str = ""
    method: str = "POST"

    def process_action(self, request):
        data = request.get_data()
        if action := data['form'].get("form.trigger"):
            if (trigger := self.triggers.get(action)) is not None:
                del data['form']["form.trigger"]
                return trigger(self, request)
        raise KeyError("No action found")
