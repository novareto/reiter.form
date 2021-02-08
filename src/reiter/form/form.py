import wtforms
import pydantic
from horseman.meta import Overhead, APIView
from reiter.view.meta import View
from reiter.form.meta import FormViewMeta
from wtforms_pydantic.converter import Converter, model_fields


class Form(wtforms.form.BaseForm):

    @classmethod
    def from_model(cls, model: pydantic.BaseModel,
                   only=(), exclude=(), **overrides):
        return cls(Converter.convert(
            model_fields(model, only=only, exclude=exclude), **overrides
        ))


class FormView(View, metaclass=FormViewMeta):

    title: str = ""
    description: str = ""
    action: str = ""
    method: str = "POST"

    def process_action(self, request: Overhead):
        data = request.get_data()
        if action := data.form.get("form.trigger", None):
            del data.form["form.trigger"]
            if (trigger := self.triggers.get(action)) is not None:
                if trigger.condition and not trigger.condition(self, request):
                    raise LookupError('Action is not allowed.')
                return trigger(self, request, data)
        raise KeyError("No action found")

    def filtered_triggers(self, request):
        for name, trigger in self.triggers.items():
            if trigger.condition and not trigger.condition(self, request):
                continue
            yield name, trigger

    def namespace(self, request, **extra):
        return {
            "actions": dict(self.filtered_triggers(request)),
            "view": self,
            "errors": None,
            "path": request.route.path,
            **extra
        }
