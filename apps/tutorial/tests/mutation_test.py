import typing
from pathlib import Path

from ulid import ULID

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import (
    ProjectTypeEnum,
)
from apps.tutorial.factories import TutorialFactory
from apps.tutorial.models import (
    Tutorial,
    TutorialStatusEnum,
)
from apps.tutorial.serializers import VALID_TUTORIAL_STATUS_TRANSITIONS
from apps.user.factories import UserFactory
from main.tests import TestCase
from utils.common import format_object_keys, to_camel_case

BASE_DIR = Path(__file__).resolve().parent


class Mutation:
    CREATE_TUTORIAL = """
        mutation CreateTutorial($data: TutorialCreateInput!) {
          createTutorial(data: $data) {
            ... on OperationInfo {
              __typename
              messages {
                code
                field
                kind
                message
              }
            }
            ... on TutorialTypeMutationResponseType {
              errors
              ok
              result {
                id
                clientId
                status
                projectId
                informationPages {
                  id
                  clientId
                  pageNumber
                  title
                  blocks {
                    id
                    clientId
                    blockType
                    blockNumber
                    text
                  }
                }
                scenarios {
                  hintDescription
                  hintIcon
                  hintTitle
                  id
                  clientId
                  instructionsDescription
                  instructionsIcon
                  instructionsTitle
                  successDescription
                  successIcon
                  scenarioPageNumber
                  successTitle
                  tasks {
                    id
                    clientId
                    reference
                    projectTypeSpecifics {
                      ... on CompareTutorialTaskPropertyType {
                        tileX
                        tileY
                        tileZ
                      }
                      ... on FindTutorialTaskPropertyType {
                        tileX
                        tileY
                        tileZ
                      }
                      ... on CompletenessTutorialTaskPropertyType {
                        tileX
                        tileY
                        tileZ
                      }
                    }
                  }
                }
              }
            }
          }
        }
    """
    UPDATE_TUTORIAL = """
        mutation UpdateTutorial($data: TutorialUpdateInput!, $pk: ID!) {
          updateTutorial(data: $data, pk: $pk) {
            ... on OperationInfo {
              __typename
              messages {
                code
                field
                kind
                message
              }
            }
            ... on TutorialTypeMutationResponseType {
              errors
              ok
              result {
                id
                clientId
                status
                projectId
                informationPages {
                  id
                  clientId
                  pageNumber
                  title
                  blocks {
                    id
                    clientId
                    blockType
                    blockNumber
                    text
                  }
                }
                scenarios {
                  hintDescription
                  hintIcon
                  hintTitle
                  id
                  clientId
                  instructionsDescription
                  instructionsIcon
                  instructionsTitle
                  successDescription
                  successIcon
                  scenarioPageNumber
                  successTitle
                  tasks {
                    id
                    clientId
                    reference
                    projectTypeSpecifics {
                      ... on CompareTutorialTaskPropertyType {
                        tileX
                        tileY
                        tileZ
                      }
                      ... on FindTutorialTaskPropertyType {
                        tileX
                        tileY
                        tileZ
                      }
                      ... on CompletenessTutorialTaskPropertyType {
                        tileX
                        tileY
                        tileZ
                      }
                    }
                  }
                }
              }
            }
          }
        }
    """


class TestTutorialMutation(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )

        # FIXME: Add more project details here
        cls.organization = OrganizationFactory.create(**cls.user_resource_kwargs)
        cls.project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            project_type=ProjectTypeEnum.FIND,
            topic="New Project",
            region="Test Region",
            project_number=1,
            requesting_organization=cls.organization,
            look_for="",
            additional_info_url="https://hi-there/about.html",
            description="The new **project** from hi-there.",
            project_type_specifics=None,
        )

    def _create_tutorial_mutation(self, tutorial_data: dict, **kwargs):
        return self.query_check(
            query=Mutation.CREATE_TUTORIAL,
            variables={
                "data": tutorial_data,
            },
        )

    def _update_tutorial_mutation(self, pk: str, tutorial_data: dict, **kwargs):
        return self.query_check(
            query=Mutation.UPDATE_TUTORIAL,
            variables={
                "data": tutorial_data,
                "pk": pk,
            },
        )

    def test_tutorial_create(self):
        tutorial_data = {
            "clientId": str(ULID()),
            "name": "My Tutorial",
            "project": self.project.pk,
            "scenarios": [
                {
                    "clientId": str(ULID()),
                    "scenarioPageNumber": 1,
                    "instructionsDescription": "Anything that is not naturally occurring",
                    "instructionsIcon": "STAR_OUTLINE",
                    "instructionsTitle": "Identify man-made structures",
                    "hintDescription": "They have sharp boundaries",
                    "hintIcon": "INFORMATION_OUTLINE",
                    "hintTitle": "Look closer!",
                    "successDescription": "You identified all man-made structures",
                    "successIcon": "CHECK",
                    "successTitle": "Well done!",
                    "tasks": [
                        {
                            "clientId": str(ULID()),
                            "projectTypeSpecifics": {"find": {"tileZ": 18, "tileX": 193196, "tileY": 110087}},
                            "reference": 0,
                        },
                        {
                            "clientId": str(ULID()),
                            "projectTypeSpecifics": {"find": {"tileZ": 18, "tileX": 193196, "tileY": 110088}},
                            "reference": 1,
                        },
                        {
                            "clientId": str(ULID()),
                            "projectTypeSpecifics": {"find": {"tileZ": 18, "tileX": 193196, "tileY": 110089}},
                            "reference": 0,
                        },
                        {
                            "clientId": str(ULID()),
                            "projectTypeSpecifics": {"find": {"tileZ": 18, "tileX": 193197, "tileY": 110087}},
                            "reference": 0,
                        },
                        {
                            "clientId": str(ULID()),
                            "projectTypeSpecifics": {"find": {"tileZ": 18, "tileX": 193197, "tileY": 110088}},
                            "reference": 1,
                        },
                        {
                            "clientId": str(ULID()),
                            "projectTypeSpecifics": {"find": {"tileZ": 18, "tileX": 193197, "tileY": 110089}},
                            "reference": 0,
                        },
                    ],
                },
                {
                    "clientId": str(ULID()),
                    "scenarioPageNumber": 2,
                    "instructionsDescription": "Anything that is not naturally occurring",
                    "instructionsIcon": "STAR_OUTLINE",
                    "instructionsTitle": "Identify natural structures",
                    "hintDescription": "They have sharp boundaries",
                    "hintIcon": "INFORMATION_OUTLINE",
                    "hintTitle": "Look closer!",
                    "successDescription": "You identified all natural structures",
                    "successIcon": "CHECK",
                    "successTitle": "Well done!",
                    "tasks": [
                        {
                            "clientId": str(ULID()),
                            "projectTypeSpecifics": {"find": {"tileZ": 18, "tileX": 193204, "tileY": 110087}},
                            "reference": 1,
                        },
                        {
                            "clientId": str(ULID()),
                            "projectTypeSpecifics": {"find": {"tileZ": 18, "tileX": 193204, "tileY": 110088}},
                            "reference": 1,
                        },
                        {
                            "clientId": str(ULID()),
                            "projectTypeSpecifics": {"find": {"tileZ": 18, "tileX": 193204, "tileY": 110089}},
                            "reference": 1,
                        },
                        {
                            "clientId": str(ULID()),
                            "projectTypeSpecifics": {"find": {"tileZ": 18, "tileX": 193205, "tileY": 110087}},
                            "reference": 1,
                        },
                        {
                            "clientId": str(ULID()),
                            "projectTypeSpecifics": {"find": {"tileZ": 18, "tileX": 193205, "tileY": 110088}},
                            "reference": 1,
                        },
                        {
                            "clientId": str(ULID()),
                            "projectTypeSpecifics": {"find": {"tileZ": 18, "tileX": 193205, "tileY": 110089}},
                            "reference": 1,
                        },
                    ],
                },
            ],
            "informationPages": [
                {
                    "clientId": str(ULID()),
                    "title": "Man-made structures",
                    "pageNumber": 1,
                    "blocks": [
                        {
                            "clientId": str(ULID()),
                            "blockNumber": 1,
                            "blockType": "TEXT",
                            "text": "Man-made structures are physical constructions created by humans, typically "
                            "using tools, materials, and engineering principles.",
                        },
                        {
                            "clientId": str(ULID()),
                            "blockNumber": 2,
                            "blockType": "TEXT",
                            "text": "These structures are built to serve specific purposes, such as housing, "
                            "transportation, defense, communication, or recreation.",
                        },
                    ],
                },
                {
                    "clientId": str(ULID()),
                    "title": "Natural structures",
                    "pageNumber": 2,
                    "blocks": [
                        {
                            "clientId": str(ULID()),
                            "blockNumber": 1,
                            "blockType": "TEXT",
                            "text": "Natural structures are physical formations that are created by nature "
                            "without human intervention",
                        },
                    ],
                },
            ],
        }

        # Creating Tutorial: Without authentication
        content = self._create_tutorial_mutation(tutorial_data)
        assert content["data"]["createTutorial"]["messages"] == [
            {
                "code": None,
                "field": "createTutorial",
                "kind": "PERMISSION",
                "message": "User is not authenticated.",
            },
        ], content

        # Creating Tutorial: With Authentication
        self.force_login(self.user)
        content = self._create_tutorial_mutation(tutorial_data)
        resp_data = content["data"]["createTutorial"]
        assert resp_data["errors"] is None, content

        latest_tutorial = Tutorial.objects.get(pk=resp_data["result"]["id"])
        assert latest_tutorial.created_by_id == self.user.pk
        assert latest_tutorial.modified_by_id == self.user.pk

        assert resp_data == self.g_mutation_response(
            ok=True,
            result=dict(
                clientId=latest_tutorial.client_id,
                id=self.gID(latest_tutorial.pk),
                status=self.genum(TutorialStatusEnum.DRAFT),
                projectId=self.gID(latest_tutorial.project_id),
                scenarios=[
                    {
                        "id": self.gID(x.pk),
                        "clientId": x.client_id,
                        "scenarioPageNumber": x.scenario_page_number,
                        "hintDescription": x.hint_description,
                        "hintIcon": self.genum(x.hint_icon),  # type: ignore[reportArgumentType]
                        "hintTitle": x.hint_title,
                        "instructionsDescription": x.instructions_description,
                        "instructionsIcon": self.genum(x.instructions_icon),  # type: ignore[reportArgumentType]
                        "instructionsTitle": x.instructions_title,
                        "successDescription": x.success_description,
                        "successIcon": self.genum(x.success_icon),  # type: ignore[reportArgumentType]
                        "successTitle": x.success_title,
                        "tasks": [
                            {
                                "id": self.gID(y.pk),
                                "clientId": y.client_id,
                                "reference": y.reference,
                                # "projectTypeSpecifics": y.project_type_specifics,
                                "projectTypeSpecifics": format_object_keys(y.project_type_specifics, to_camel_case),
                            }
                            for y in x.tasks.all()
                        ],
                    }
                    for x in latest_tutorial.scenarios.all()
                ],
                informationPages=[
                    {
                        "clientId": x.client_id,
                        "id": self.gID(x.pk),
                        "pageNumber": x.page_number,
                        "title": x.title,
                        "blocks": [
                            {
                                "id": self.gID(y.pk),
                                "clientId": y.client_id,
                                "blockNumber": y.block_number,
                                "blockType": self.genum(y.block_type),  # type: ignore[reportArgumentType]
                                "text": y.text,
                                # FIXME(tnagorra): Handle image
                            }
                            for y in x.blocks.all()
                        ],
                    }
                    for x in latest_tutorial.information_pages.all()
                ],
            ),
        ), content

        def get_update_for_task(tut: dict):
            return {"update": {**tut, "projectTypeSpecifics": {"find": tut.get("projectTypeSpecifics")}}}

        # Updating Tutorial: Without authentication
        tutorial_from_res = resp_data["result"]
        project = tutorial_from_res.pop("projectId")
        tutorial_from_res.pop("id")
        tutorial_data = {
            **tutorial_from_res,
            "project": project,
            "scenarios": [
                {
                    "update": {
                        **tutorial_from_res["scenarios"][0],
                        "tasks": [
                            get_update_for_task(tutorial_from_res["scenarios"][0]["tasks"][0]),
                            get_update_for_task(tutorial_from_res["scenarios"][0]["tasks"][1]),
                            get_update_for_task(tutorial_from_res["scenarios"][0]["tasks"][2]),
                            get_update_for_task(tutorial_from_res["scenarios"][0]["tasks"][3]),
                            get_update_for_task(tutorial_from_res["scenarios"][0]["tasks"][4]),
                            get_update_for_task(tutorial_from_res["scenarios"][0]["tasks"][5]),
                        ],
                    },
                },
                {
                    "update": {
                        **tutorial_from_res["scenarios"][1],
                        "tasks": [
                            get_update_for_task(tutorial_from_res["scenarios"][1]["tasks"][0]),
                            get_update_for_task(tutorial_from_res["scenarios"][1]["tasks"][1]),
                            get_update_for_task(tutorial_from_res["scenarios"][1]["tasks"][2]),
                            get_update_for_task(tutorial_from_res["scenarios"][1]["tasks"][3]),
                            get_update_for_task(tutorial_from_res["scenarios"][1]["tasks"][4]),
                            get_update_for_task(tutorial_from_res["scenarios"][1]["tasks"][5]),
                        ],
                    },
                },
            ],
            "informationPages": [
                {
                    "update": {
                        **tutorial_from_res["informationPages"][0],
                        "blocks": [
                            {
                                "update": {
                                    **tutorial_from_res["informationPages"][0]["blocks"][0],
                                },
                            },
                            {
                                "delete": {
                                    "id": tutorial_from_res["informationPages"][0]["blocks"][1]["id"],
                                },
                            },
                            {
                                "create": {
                                    "clientId": str(ULID()),
                                    # NOTE: blockNumber 2 is previously deleted so should not error on unique constraint
                                    "blockNumber": 2,
                                    "blockType": "TEXT",
                                    "text": "These structures are built to serve various purposes",
                                },
                            },
                        ],
                    },
                },
                {
                    "update": {
                        **tutorial_from_res["informationPages"][1],
                        "blocks": [
                            {
                                "update": {
                                    **tutorial_from_res["informationPages"][1]["blocks"][0],
                                },
                            },
                        ],
                    },
                },
            ],
        }

        self.logout()
        content = self._update_tutorial_mutation(str(latest_tutorial.pk), tutorial_data)
        assert content["data"]["updateTutorial"]["messages"] == [
            {
                "code": None,
                "field": "updateTutorial",
                "kind": "PERMISSION",
                "message": "User is not authenticated.",
            },
        ], content

        # Creating Tutorial: With Authentication
        self.force_login(self.user)
        content = self._update_tutorial_mutation(str(latest_tutorial.pk), tutorial_data)
        resp_data = content["data"]["updateTutorial"]
        assert resp_data["errors"] is None, content

        latest_tutorial.refresh_from_db()

        assert resp_data == self.g_mutation_response(
            ok=True,
            result=dict(
                clientId=latest_tutorial.client_id,
                id=self.gID(latest_tutorial.pk),
                status=self.genum(TutorialStatusEnum.DRAFT),
                projectId=self.gID(latest_tutorial.project_id),
                scenarios=[
                    {
                        "id": self.gID(x.pk),
                        "clientId": x.client_id,
                        "scenarioPageNumber": x.scenario_page_number,
                        "hintDescription": x.hint_description,
                        "hintIcon": self.genum(x.hint_icon),  # type: ignore[reportArgumentType]
                        "hintTitle": x.hint_title,
                        "instructionsDescription": x.instructions_description,
                        "instructionsIcon": self.genum(x.instructions_icon),  # type: ignore[reportArgumentType]
                        "instructionsTitle": x.instructions_title,
                        "successDescription": x.success_description,
                        "successIcon": self.genum(x.success_icon),  # type: ignore[reportArgumentType]
                        "successTitle": x.success_title,
                        "tasks": [
                            {
                                "id": self.gID(y.pk),
                                "clientId": y.client_id,
                                "reference": y.reference,
                                "projectTypeSpecifics": format_object_keys(y.project_type_specifics, to_camel_case),
                            }
                            for y in x.tasks.all()
                        ],
                    }
                    for x in latest_tutorial.scenarios.all()
                ],
                informationPages=[
                    {
                        "id": self.gID(x.pk),
                        "clientId": x.client_id,
                        "pageNumber": x.page_number,
                        "title": x.title,
                        "blocks": [
                            {
                                "id": self.gID(y.pk),
                                "clientId": y.client_id,
                                "blockNumber": y.block_number,
                                "blockType": self.genum(y.block_type),  # type: ignore[reportArgumentType]
                                "text": y.text,
                                # FIXME(tnagorra): Handle image
                            }
                            for y in x.blocks.all()
                        ],
                    }
                    for x in latest_tutorial.information_pages.all()
                ],
            ),
        ), content

        # Test the tutorial with different project_type
        compare_project = ProjectFactory.create(
            **self.user_resource_kwargs,
            project_type=ProjectTypeEnum.COMPARE,
            requesting_organization=self.organization,
            topic="Compare Project 101",
            look_for="",
            additional_info_url="https://hi-there/about.html",
            description="The new **project** from hi-there.",
            project_type_specifics=None,
        )
        tutorial_data["project"] = self.gID(compare_project.pk)
        content = self._update_tutorial_mutation(str(latest_tutorial.pk), tutorial_data)
        assert content["data"]["updateTutorial"]["errors"] is not None, content

    def test_tutorial_state_transitions(self):
        # Create a draft tutorial
        tutorial = TutorialFactory.create(
            client_id=str(ULID()),
            name="Status Tutorial",
            project=self.project,
            created_by=self.user,
            modified_by=self.user,
            status=TutorialStatusEnum.DRAFT,
        )

        # Checking with authenticated user
        self.force_login(self.user)
        for status, new_status in VALID_TUTORIAL_STATUS_TRANSITIONS:
            tutorial.status = status
            tutorial.save(update_fields=["status"])
            data = {
                "clientId": tutorial.client_id,
                "project": self.gID(tutorial.project_id),
                "status": self.genum(new_status),
            }
            response = self._update_tutorial_mutation(str(tutorial.pk), data)

            resp_data = response["data"]["updateTutorial"]
            assert resp_data["errors"] is None, response
            tutorial.refresh_from_db()
            assert tutorial.status == new_status

        invalid_transitions = [
            (TutorialStatusEnum.PUBLISHED, TutorialStatusEnum.DRAFT),
            (TutorialStatusEnum.ARCHIVED, TutorialStatusEnum.PUBLISHED),
            (TutorialStatusEnum.DRAFT, TutorialStatusEnum.ARCHIVED),
        ]

        for old_status, new_status in invalid_transitions:
            tutorial.status = old_status
            tutorial.save(update_fields=["status"])
            data = {
                "clientId": tutorial.client_id,
                "project": self.gID(tutorial.project_id),
                "status": self.genum(new_status),
            }
            response = self._update_tutorial_mutation(str(tutorial.pk), data)

            resp_data = response["data"]["updateTutorial"]
            assert resp_data["errors"] is not None, response
            assert "Tutorial status cannot be changed" in resp_data["errors"][0]["messages"], response
            tutorial.refresh_from_db()
            assert tutorial.status == old_status
