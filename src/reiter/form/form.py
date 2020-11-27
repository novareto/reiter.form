import wtforms
import pydantic
from horseman.meta import Overhead, APIView
from wtforms_pydantic.converter import Converter, model_fields
from reiter.form.meta import FormViewMeta


class Form(wtforms.form.BaseForm):

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

    def process_action(self, request: Overhead):
        data = request.get_data()
        if action := data['form'].get("form.trigger"):
            if (trigger := self.triggers.get(action)) is not None:
                del data['form']["form.trigger"]
                return trigger(self, request)
        raise KeyError("No action found")
