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


class FormMeta(wtforms.meta.DefaultMeta):

    def render_field(inst, field, render_kw):
        class_ = "form-control"
        if field.errors:
            class_ += " is-invalid"
        render_kw.update({"class_": class_})
        return field.widget(field, **render_kw)


class Form(wtforms.form.BaseForm):

    def __init__(self, fields, prefix="", meta=FormMeta()):
        super().__init__(fields, prefix, meta)

    @classmethod
    def from_model(cls, model: pydantic.BaseModel,
                   only=(), exclude=(), **overrides):
        return cls(Converter.convert(
            model_fields(model, only=only, exclude=exclude), **overrides
        ))


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
