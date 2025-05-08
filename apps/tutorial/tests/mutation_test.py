import pprint
import typing
from pathlib import Path

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import (
    ProjectTypeEnum,
)
from apps.tutorial.models import (
    Tutorial,
)
from apps.user.factories import UserFactory
from main.tests import TestCase

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
                isDraft
                projectId
                informationPages {
                  id
                  pageNumber
                  title
                  blocks {
                    id
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
                  instructionsDescription
                  instructionsIcon
                  instructionsTitle
                  successDescription
                  successIcon
                  scenarioId
                  successTitle
                  tasks {
                    id
                    reference
                    projectTypeSpecifics
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
                isDraft
                projectId
                informationPages {
                  id
                  pageNumber
                  title
                  blocks {
                    id
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
                  instructionsDescription
                  instructionsIcon
                  instructionsTitle
                  successDescription
                  successIcon
                  scenarioId
                  successTitle
                  tasks {
                    id
                    reference
                    projectTypeSpecifics
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
            requesting_organization=cls.organization,
            name="New Project 101",
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
            "project": self.project.pk,
            "isDraft": False,
            "scenarios": [
                {
                    "scenarioId": 1,
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
                        {"projectTypeSpecifics": {"tile_z": 18, "tile_x": 193196, "tile_y": 110087}, "reference": 0},
                        {"projectTypeSpecifics": {"tile_z": 18, "tile_x": 193196, "tile_y": 110088}, "reference": 1},
                        {"projectTypeSpecifics": {"tile_z": 18, "tile_x": 193196, "tile_y": 110089}, "reference": 0},
                        {"projectTypeSpecifics": {"tile_z": 18, "tile_x": 193197, "tile_y": 110087}, "reference": 0},
                        {"projectTypeSpecifics": {"tile_z": 18, "tile_x": 193197, "tile_y": 110088}, "reference": 1},
                        {"projectTypeSpecifics": {"tile_z": 18, "tile_x": 193197, "tile_y": 110089}, "reference": 0},
                    ],
                },
                {
                    "scenarioId": 2,
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
                        {"projectTypeSpecifics": {"tile_z": 18, "tile_x": 193204, "tile_y": 110087}, "reference": 1},
                        {"projectTypeSpecifics": {"tile_z": 18, "tile_x": 193204, "tile_y": 110088}, "reference": 1},
                        {"projectTypeSpecifics": {"tile_z": 18, "tile_x": 193204, "tile_y": 110089}, "reference": 1},
                        {"projectTypeSpecifics": {"tile_z": 18, "tile_x": 193205, "tile_y": 110087}, "reference": 1},
                        {"projectTypeSpecifics": {"tile_z": 18, "tile_x": 193205, "tile_y": 110088}, "reference": 1},
                        {"projectTypeSpecifics": {"tile_z": 18, "tile_x": 193205, "tile_y": 110089}, "reference": 1},
                    ],
                },
            ],
            "informationPages": [
                {
                    "title": "Man-made structures",
                    "pageNumber": 1,
                    "blocks": [
                        {
                            "blockNumber": 1,
                            "blockType": "TEXT",
                            "text": "Man-made structures are physical constructions created by humans, typically "
                            "using tools, materials, and engineering principles.",
                        },
                        {
                            "blockNumber": 2,
                            "blockType": "TEXT",
                            "text": "These structures are built to serve specific purposes, such as housing, "
                            "transportation, defense, communication, or recreation.",
                        },
                    ],
                },
                {
                    "title": "Natural structures",
                    "pageNumber": 2,
                    "blocks": [
                        {
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
        pprint.pp(resp_data["errors"])
        assert resp_data["errors"] is None, content

        latest_tutorial = Tutorial.objects.get(pk=resp_data["result"]["id"])
        assert latest_tutorial.created_by_id == self.user.pk
        assert latest_tutorial.modified_by_id == self.user.pk

        assert resp_data == self.g_mutation_response(
            ok=True,
            result=dict(
                id=self.gID(latest_tutorial.pk),
                isDraft=latest_tutorial.is_draft,
                projectId=self.gID(latest_tutorial.project_id),
                scenarios=[
                    {
                        "id": self.gID(x.pk),
                        "scenarioId": x.scenario_id,
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
                                "reference": y.reference,
                                "projectTypeSpecifics": y.project_type_specifics,
                            }
                            for y in x.tasks.all()
                        ],
                    }
                    for x in latest_tutorial.scenarios.all()
                ],
                informationPages=[
                    {
                        "id": self.gID(x.pk),
                        "pageNumber": x.page_number,
                        "title": x.title,
                        "blocks": [
                            {
                                "id": self.gID(y.pk),
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

        # Updating Tutorial: Without authentication
        tutorial_from_res = resp_data["result"]
        project = tutorial_from_res.pop("projectId")
        tutorial_data = {
            **tutorial_from_res,
            "project": project,
            "scenarios": [
                {
                    "update": {
                        **tutorial_from_res["scenarios"][0],
                        "tasks": [
                            {"update": {**tutorial_from_res["scenarios"][0]["tasks"][0]}},
                            {"update": {**tutorial_from_res["scenarios"][0]["tasks"][1]}},
                            {"update": {**tutorial_from_res["scenarios"][0]["tasks"][2]}},
                            {"update": {**tutorial_from_res["scenarios"][0]["tasks"][3]}},
                            {"update": {**tutorial_from_res["scenarios"][0]["tasks"][4]}},
                            {"update": {**tutorial_from_res["scenarios"][0]["tasks"][5]}},
                        ],
                    },
                },
                {
                    "update": {
                        **tutorial_from_res["scenarios"][1],
                        "tasks": [
                            {"update": {**tutorial_from_res["scenarios"][1]["tasks"][0]}},
                            {"update": {**tutorial_from_res["scenarios"][1]["tasks"][1]}},
                            {"update": {**tutorial_from_res["scenarios"][1]["tasks"][2]}},
                            {"update": {**tutorial_from_res["scenarios"][1]["tasks"][3]}},
                            {"update": {**tutorial_from_res["scenarios"][1]["tasks"][4]}},
                            {"update": {**tutorial_from_res["scenarios"][1]["tasks"][5]}},
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
        pprint.pp(resp_data["errors"])
        assert resp_data["errors"] is None, content

        latest_tutorial.refresh_from_db()

        assert resp_data == self.g_mutation_response(
            ok=True,
            result=dict(
                id=self.gID(latest_tutorial.pk),
                isDraft=latest_tutorial.is_draft,
                projectId=self.gID(latest_tutorial.project_id),
                scenarios=[
                    {
                        "id": self.gID(x.pk),
                        "scenarioId": x.scenario_id,
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
                                "reference": y.reference,
                                "projectTypeSpecifics": y.project_type_specifics,
                            }
                            for y in x.tasks.all()
                        ],
                    }
                    for x in latest_tutorial.scenarios.all()
                ],
                informationPages=[
                    {
                        "id": self.gID(x.pk),
                        "pageNumber": x.page_number,
                        "title": x.title,
                        "blocks": [
                            {
                                "id": self.gID(y.pk),
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
