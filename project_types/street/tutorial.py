from apps.tutorial.models import Tutorial
from project_types.base import tutorial as base_tutorial
from project_types.street.project import StreetProjectProperty


class StreetTutorialTaskProperty(base_tutorial.BaseTutorialTaskProperty):
    identifier: int
    object_geometry: str


class StreetTutorial(
    base_tutorial.BaseTutorial[
        StreetProjectProperty,
        StreetTutorialTaskProperty,
    ],
):
    project_property_class = StreetProjectProperty
    tutorial_task_property_class = StreetTutorialTaskProperty

    def __init__(self, tutorial: Tutorial):
        super().__init__(tutorial)
