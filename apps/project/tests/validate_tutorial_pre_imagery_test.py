import typing

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import Project, ProjectTypeEnum
from apps.project.tests.mutation_test import Mutation
from apps.tutorial.factories import TutorialFactory
from apps.tutorial.models import Tutorial
from apps.user.factories import UserFactory
from main.tests import TestCase

POST_EVENT_TILE_SERVER_PROPERTY = {"name": "BING", "bing": {"credits": "Bing"}}
PRE_EVENT_TILE_SERVER_PROPERTY = {"name": "ESRI", "esri": {"credits": "ESRI"}}

WITHOUT_PRE_IMAGERY_SPECIFICS = {
    "object_source": {
        "source_type": "OBJECT_GEOJSON_URL",
        "object_geojson_url": "https://example.com/buildings.geojson",
    },
    "tile_server_property": POST_EVENT_TILE_SERVER_PROPERTY,
}

WITH_PRE_IMAGERY_SPECIFICS = {
    **WITHOUT_PRE_IMAGERY_SPECIFICS,
    "has_pre_imagery": True,
    "pre_event_tile_server_property": PRE_EVENT_TILE_SERVER_PROPERTY,
}

# NOTE: Validate projects saved before pre-event imagery do not have has_pre_imagery
LEGACY_SPECIFICS = WITHOUT_PRE_IMAGERY_SPECIFICS


def _specifics_input(*, has_pre_imagery: bool) -> dict[str, typing.Any]:
    validate: dict[str, typing.Any] = {
        "objectSource": {
            "sourceType": "OBJECT_GEOJSON_URL",
            "objectGeojsonUrl": "https://example.com/buildings.geojson",
        },
        "tileServerProperty": POST_EVENT_TILE_SERVER_PROPERTY,
        "hasPreImagery": has_pre_imagery,
    }
    if has_pre_imagery:
        validate["preEventTileServerProperty"] = PRE_EVENT_TILE_SERVER_PROPERTY
    return {"validate": validate}


class TestValidateTutorialPreImagery(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )
        cls.organization = OrganizationFactory.create(**cls.user_resource_kwargs)

    @typing.override
    def setUp(self):
        super().setUp()
        self.force_login(self.user)

    def _create_project(
        self,
        project_type_specifics: dict[str, typing.Any],
        *,
        status: Project.Status = Project.Status.DRAFT,
        **kwargs: typing.Any,
    ) -> Project:
        return ProjectFactory.create(
            **self.user_resource_kwargs,
            project_type=ProjectTypeEnum.VALIDATE,
            project_type_specifics=project_type_specifics,
            requesting_organization=self.organization,
            status=status,
            **kwargs,
        )

    def _create_tutorial(self, project: Project, name: str) -> Tutorial:
        return TutorialFactory.create(
            **self.user_resource_kwargs,
            project=project,
            name=name,
            status=Tutorial.Status.PUBLISHED,
        )

    def _mutate(self, query: str, mutation_name: str, project: Project, data: dict[str, typing.Any]):
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(
                query,
                variables={
                    "pk": str(project.pk),
                    "data": {"clientId": project.client_id, **data},
                },
            )
        return content["data"][mutation_name]

    def _update_project(self, project: Project, data: dict[str, typing.Any]):
        return self._mutate(Mutation.UPDATE_PROJECT, "updateProject", project, data)

    def _update_processed_project(self, project: Project, data: dict[str, typing.Any]):
        return self._mutate(Mutation.UPDATE_PROCESSED_PROJECT, "updateProcessedProject", project, data)

    def _update_project_status(self, project: Project, status: Project.Status):
        return self._mutate(Mutation.UPDATE_PROJECT_STATUS, "updateProjectStatus", project, {"status": self.genum(status)})

    @staticmethod
    def _error_messages(response: dict[str, typing.Any]) -> dict[str, str]:
        return {error["field"]: error["messages"] for error in response["errors"] or []}

    def test_attach_tutorial_with_pre_imagery_to_project_without(self):
        tutorial = self._create_tutorial(self._create_project(WITH_PRE_IMAGERY_SPECIFICS), "Before and after")
        project = self._create_project(WITHOUT_PRE_IMAGERY_SPECIFICS)

        response = self._update_project(project, {"tutorial": self.gID(tutorial.pk)})
        assert self._error_messages(response) == {
            "tutorial": (
                "The project has no pre-event imagery, but tutorial 'Before and after' was created for a project with"
                " pre-event imagery."
            ),
        }, response

        project.refresh_from_db()
        assert project.tutorial is None

    def test_attach_tutorial_without_pre_imagery_to_project_with(self):
        tutorial = self._create_tutorial(self._create_project(WITHOUT_PRE_IMAGERY_SPECIFICS), "After only")
        project = self._create_project(WITH_PRE_IMAGERY_SPECIFICS)

        response = self._update_project(project, {"tutorial": self.gID(tutorial.pk)})
        assert self._error_messages(response) == {
            "tutorial": (
                "The project has pre-event imagery, but tutorial 'After only' was created for a project without"
                " pre-event imagery."
            ),
        }, response

    def test_attach_tutorial_with_matching_pre_imagery(self):
        for specifics in [WITH_PRE_IMAGERY_SPECIFICS, WITHOUT_PRE_IMAGERY_SPECIFICS]:
            tutorial = self._create_tutorial(self._create_project(specifics), "Tutorial")
            project = self._create_project(specifics)

            response = self._update_project(project, {"tutorial": self.gID(tutorial.pk)})
            assert response["ok"], response

            project.refresh_from_db()
            assert project.tutorial == tutorial

    def test_attach_tutorial_of_legacy_project_to_project_without_pre_imagery(self):
        tutorial = self._create_tutorial(self._create_project(LEGACY_SPECIFICS), "Legacy")
        project = self._create_project(WITHOUT_PRE_IMAGERY_SPECIFICS)

        response = self._update_project(project, {"tutorial": self.gID(tutorial.pk)})
        assert response["ok"], response

    def test_add_pre_imagery_to_project_with_tutorial_without(self):
        tutorial = self._create_tutorial(self._create_project(WITHOUT_PRE_IMAGERY_SPECIFICS), "After only")
        project = self._create_project(WITHOUT_PRE_IMAGERY_SPECIFICS, tutorial=tutorial)

        response = self._update_project(project, {"projectTypeSpecifics": _specifics_input(has_pre_imagery=True)})
        assert self._error_messages(response) == {
            "tutorial": (
                "The project has pre-event imagery, but tutorial 'After only' was created for a project without"
                " pre-event imagery."
            ),
        }, response

        # NOTE: Changing both together is allowed
        other_tutorial = self._create_tutorial(self._create_project(WITH_PRE_IMAGERY_SPECIFICS), "Before and after")
        response = self._update_project(
            project,
            {
                "projectTypeSpecifics": _specifics_input(has_pre_imagery=True),
                "tutorial": self.gID(other_tutorial.pk),
            },
        )
        assert response["ok"], response

    def test_change_pre_imagery_of_project_with_its_own_tutorial(self):
        project = self._create_project(WITHOUT_PRE_IMAGERY_SPECIFICS)
        project.tutorial = self._create_tutorial(project, "Own tutorial")
        project.save(update_fields=["tutorial"])

        response = self._update_project(project, {"projectTypeSpecifics": _specifics_input(has_pre_imagery=True)})
        assert response["ok"], response

    def test_change_pre_imagery_of_project_whose_tutorial_is_used(self):
        source_project = self._create_project(WITHOUT_PRE_IMAGERY_SPECIFICS)
        tutorial = self._create_tutorial(source_project, "After only")
        using_project = self._create_project(WITHOUT_PRE_IMAGERY_SPECIFICS, tutorial=tutorial)

        response = self._update_project(
            source_project,
            {"projectTypeSpecifics": _specifics_input(has_pre_imagery=True)},
        )
        assert self._error_messages(response) == {
            "projectTypeSpecifics": (
                "Cannot add pre-event imagery, because these projects without pre-event imagery use a tutorial"
                f" created for this project: {using_project.generate_name()} (tutorial 'After only')"
            ),
        }, response

        # NOTE: Once the project using the tutorial agrees, the change is allowed
        using_project.project_type_specifics = WITH_PRE_IMAGERY_SPECIFICS
        using_project.save(update_fields=["project_type_specifics"])
        response = self._update_project(
            source_project,
            {"projectTypeSpecifics": _specifics_input(has_pre_imagery=True)},
        )
        assert response["ok"], response

    def test_attach_tutorial_to_processed_project(self):
        mismatched_tutorial = self._create_tutorial(self._create_project(WITH_PRE_IMAGERY_SPECIFICS), "Before and after")
        tutorial = self._create_tutorial(self._create_project(WITHOUT_PRE_IMAGERY_SPECIFICS), "After only")
        project = self._create_project(WITHOUT_PRE_IMAGERY_SPECIFICS, status=Project.Status.PROCESSED)

        response = self._update_processed_project(project, {"tutorial": self.gID(mismatched_tutorial.pk)})
        assert self._error_messages(response) == {
            "tutorial": (
                "The project has no pre-event imagery, but tutorial 'Before and after' was created for a project with"
                " pre-event imagery."
            ),
        }, response

        response = self._update_processed_project(project, {"tutorial": self.gID(tutorial.pk)})
        assert response["ok"], response

    def test_publish_project_with_mismatched_tutorial(self):
        tutorial = self._create_tutorial(self._create_project(WITH_PRE_IMAGERY_SPECIFICS), "Before and after")
        # NOTE: A mismatched pair can only be saved outside the mutations
        project = self._create_project(WITHOUT_PRE_IMAGERY_SPECIFICS, status=Project.Status.PROCESSED, tutorial=tutorial)

        response = self._update_project_status(project, Project.Status.READY_TO_PUBLISH)
        assert self._error_messages(response) == {
            "tutorial": (
                "The project has no pre-event imagery, but tutorial 'Before and after' was created for a project with"
                " pre-event imagery."
            ),
        }, response

        project.refresh_from_db()
        assert project.status_enum == Project.Status.PROCESSED
