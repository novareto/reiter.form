from pydantic import BaseModel, create_model
from typing import Type, NamedTuple, ClassVar
from reiter.form.form import Form, FormView
from reiter.form.meta import Trigger
from horseman.http import Multidict
import horseman.response


class ModelStep:

    def __init__(self, name: str, model: BaseModel, title: str, desc: str):
        self.model = model
        self.name = name
        self.title = title
        self.desc = desc

    def select(self, *names):
        fields = {
            name: (self.model.__fields__[name].type_,
                   self.model.__fields__[name].field_info)
            for name in names
        }
        return create_model(
            self.name,
            title=(ClassVar[str], self.title),
            description=(ClassVar[str], self.desc),
            **fields
        )

    def omit(self, *names):
        fields = {
            name: (self.model.__fields__[name].type_,
                   self.model.__fields__[name].field_info)
            for name in self.model.__fields__.keys()
            if name not in names
        }
        return create_model(
            self.name,
            title=(ClassVar[str], self.title),
            description=(ClassVar[str], self.desc),
            **fields
        )


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
        assert self.current_index <= len(self.steps)
        self.data = self.get_data()

    def get_data(self):
        return self.request.session.get(self.session_key, {})

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


class ModelWizard(Wizard):
    model: Type[BaseModel]

    def get_data(self):
        data = self.request.session.get(self.session_key)
        if data is None:
            return self.model()
        return self.model.construct(**data)

    def save_step(self, data: dict):
        for name, value in data.items():
            setattr(self.data, name, value)
        self.request.session[self.session_key] = self.data.dict()
        self.request.session.save()

    @property
    def current_step(self):
        model = self.steps[self.current_index - 1]
        data = {
            name: getattr(self.data, name)
            for name in model.__fields__.keys()
            if getattr(self.data, name, ...) is not ...
        }
        return Step(
            index=self.current_index,
            model=model,
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
    factory: Type[Wizard]

    @property
    def title(self):
        return self.current_step.model.title

    @property
    def description(self):
        return self.current_step.model.description

    @property
    def counter(self):
        return f"Schrit {self.wizard.current_step.index} / {len(self.wizard.steps)}"

    def update(self):
        self.wizard = self.factory(self.request)
        self.current_step = self.wizard.current_step

    def setupForm(self, formdata=Multidict()):
        form = self.formclass.from_model(self.current_step.model)
        form.process(data=self.current_step.data, formdata=formdata)
        return form

    @Trigger.trigger(
        "previous", "Previous", order=1, css="btn btn-secondary",
        condition=is_not_first_step)
    def previous(self, request, data):
        return horseman.response.redirect(
            f"{request.route.path}?step={self.current_step.index - 1}"
        )

    @Trigger.trigger(
        "Next", "Next", order=2, css="btn btn-primary",
        condition=is_not_last_step)
    def next(self, request, data):
        form = self.setupForm(formdata=data.form)
        if not form.validate():
            return {'form': form, 'wizard': self.wizard}
        self.wizard.save_step(data.form.dict())
        return horseman.response.redirect(
            f"{request.route.path}?step={self.current_step.index + 1}"
        )

    @Trigger.trigger(
        "finish", "Finish", order=2, css="btn btn-primary",
        condition=is_last_step)
    def finish(self, request, data):
        form = self.setupForm(formdata=data.form)
        if not form.validate():
            return {'form': form, 'wizard': self.wizard}
        return self.wizard.save(data.form.dict())
