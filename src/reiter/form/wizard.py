from abc import ABC, abstractmethod, abstractproperty
from horseman.http import Multidict
from horseman.meta import Overhead
from typing import Any, Type, NamedTuple, ClassVar, Tuple, NoReturn, Dict
from reiter.form.form import FormView
from reiter.form.meta import Trigger
from wtforms import BaseForm, Field


StepData = Dict[str: Any]
WizardData = Dict[int, StepData]


class Step(NamedTuple):
    index: int
    data: StepData
    title: str
    description: str
    fields: Dict[str, Field]


class Wizard(ABC):

    data: WizardData
    current_index: int
    request:Overhead
    steps: ClassVar[Tuple[Step]]

    def __init__(self, request):
        self.request = request
        self.data = self.get_data()
        self.current_index = self.step(request)
        self.current_step = self.steps[self.current_index]._replace(
            data=self.data.get(self.current_index, {})
        )

    @abstractmethod
    def step(self, request) -> int:
        pass

    @abstractmethod
    def get_data(self) -> WizardData:
        pass

    @abstractmethod
    def save_step(self, data: StepData) -> NoReturn:
        pass

    @abstractmethod
    def conclude(self) -> NoReturn:
        pass

    def save(self, data: StepData) -> NoReturn:
        self.save_step(data)
        return self.conclude()


def is_not_first_step(view, request):
    return Wizard.step(request) != 1


def is_not_last_step(view, request):
    return Wizard.step(request) < len(view.wizard.steps)


def is_last_step(view, request):
    return Wizard.step(request) == len(view.wizard.steps)


class WizardForm(FormView):

    formclass: Type[BaseForm]
    factory: Type[Wizard]

    def redirect_to_step(self, step: int):
        raise NotImplementedError('Implement your own.')

    def update(self):
        self.wizard: Wizard = self.factory(self.request)
        self.current_step: Step = self.wizard.current_step
        self.description = self.current_step.description
        self.title = self.current_step.title

    def setupForm(self, formdata=Multidict()):
        form = self.formclass(self.current_step.fields)
        form.process(data=self.current_step.data, formdata=formdata)
        return form

    @Trigger.trigger(
        "previous", "Previous", order=1, css="btn btn-secondary",
        condition=is_not_first_step)
    def previous(self, request, data):
        return self.redirect_to_step(self.current_step.index - 1)

    @Trigger.trigger(
        "Next", "Next", order=2, css="btn btn-primary",
        condition=is_not_last_step)
    def next(self, request, data):
        form = self.setupForm(formdata=data.form)
        if not form.validate():
            return {'form': form, 'wizard': self.wizard}
        self.wizard.save_step(form.data)
        return self.redirect_to_step(self.current_step.index + 1)

    @Trigger.trigger(
        "finish", "Finish", order=2, css="btn btn-primary",
        condition=is_last_step)
    def finish(self, request, data):
        form = self.setupForm(formdata=data.form)
        if not form.validate():
            return {'form': form, 'wizard': self.wizard}
        return self.wizard.save(form.data)
