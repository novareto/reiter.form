from horseman.meta import Overhead
from reiter.view.meta import APIView
from reiter.form.meta import TriggersScope, Triggers


class FormView(APIView, metaclass=TriggersScope):

    title: str = ""
    description: str = ""
    action: str = ""
    method: str = "POST"
    triggers: Triggers

    def POST(self):
        """Retrieves the action name and potentially calls process_action.
        """
        raise NotImplementedError(
            'POST method should be implemented by your class.')

    def process_action(self, action: str):
        if (trigger := self.triggers.get(action)) is not None:
            if trigger.condition and not trigger.condition(self, request):
                raise RuntimeError('Action is not allowed.')
            return trigger(self, self.request, self.request.get_data())
        raise LookupError("No action found")

    def namespace(self, **extra):
        return {
            "actions": dict(self.triggers.filtered(self, self.request)),
            "request": self.request,
            "view": self,
            **extra
        }
