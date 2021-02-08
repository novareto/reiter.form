from enum import IntEnum
from pydantic import BaseModel
from typing import Optional, Type, NamedTuple, ClassVar
from reiter.form.form import Form, FormView
from reiter.form.meta import Trigger
from horseman.http import Multidict
import horseman.response


class Step(NamedTuple):
    index: int
    model: BaseModel
    data: dict

    def __call__(self, data=None):
        if data is not None:
            return self.model(**data)
        return self.model(**self.data)


class Wizard:

    session_key: ClassVar[str]
    steps: ClassVar[tuple]

    @staticmethod
    def step(request):
        if 'step' in request.query:
            return request.query.int('step')
        return 1

    def __init__(self, request):
        self.request = request
        self.current_index = self.step(request)
        self.data = request.session.get(self.session_key, {})
        assert self.current_index <= len(self.steps)

    def save_step(self, data: dict):
        self.data[self.current_index] = data
        self.request.session[self.session_key] = self.data
        self.request.session.save()

    def save(self, data: dict):
        self.save_step(data)
        return self.conclude()

    def conclude(self) -> horseman.response.Response:
        raise NotImplementedError()

    @property
    def current_step(self):
        data = self.data.get(self.current_index, {})
        return Step(
            index=self.current_index,
            model=self.steps[self.current_index - 1],
            data=data
        )


def is_not_first_step(view, request):
    return Wizard.step(request) != 1


def is_not_last_step(view, request):
    return Wizard.step(request) < len(view.wizard.steps)


def is_last_step(view, request):
    return Wizard.step(request) == len(view.wizard.steps)


class WizardForm(FormView):

    formclass: Type[Form] = Form
    wizard: Wizard

    def setupForm(self, step: Step, formdata=Multidict()):
        form = self.formclass.from_model(step.model)
        form.process(data=step.data, formdata=formdata)
        return form

    @Trigger.trigger(
        "previous", "Previous", order=1, css="btn btn-secondary",
        condition=is_not_first_step)
    def previous(self, request, data):
        step = self.wizard.step(request)
        return horseman.response.Response.create(
            302, headers={"Location": f"{request.route.path}?step={step - 1}"}
        )

    @Trigger.trigger(
        "Next", "Next", order=2, css="btn btn-primary",
        condition=is_not_last_step)
    def next(self, request, data):
        wizard = self.wizard(request)
        form = self.setupForm(wizard.current_step, formdata=data.form)
        if not form.validate():
            return self.namespace(
                request, form=form, wizard=wizard, error=None)
        wizard.save_step(data.form.dict())
        return horseman.response.Response.create(
            302, headers={
                "Location": f"{request.route.path}?step={wizard.current_index + 1}"}
        )

    @Trigger.trigger(
        "finish", "Finish", order=2, css="btn btn-primary",
        condition=is_last_step)
    def finish(self, request, data):
        wizard = self.wizard(request)
        form = self.setupForm(wizard.current_step, formdata=data.form)
        if not form.validate():
            return self.namespace(
                request, form=form, wizard=wizard, error=None)
        return wizard.save(data.form.dict())
