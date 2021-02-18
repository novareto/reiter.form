from horseman.meta import Overhead
from reiter.view.meta import View
from reiter.form.meta import FormViewMeta
from wtforms_pydantic import Form


Form  # BBB: backward compatible import.


class FormView(View, metaclass=FormViewMeta):

    title: str = ""
    description: str = ""
    action: str = ""
    method: str = "POST"

    def POST(self):
        self.request.extract()
        return self.process_action(self.request)

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

    def namespace(self, **extra):
        return {
            "actions": dict(self.filtered_triggers(self.request)),
            "errors": None,
            "path": self.request.route.path,
            "request": self.request,
            "view": self,
            **extra
        }
