import random
import typing

from apps.common.models import IconEnum
from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import (
    ProjectTypeEnum,
)
from apps.tutorial.factories import (
    TutorialFactory,
    TutorialInformationPageBlockFactory,
    TutorialInformationPageFactory,
    TutorialScenarioPageFactory,
    TutorialTaskFactory,
)
from apps.tutorial.models import (
    TutorialInformationPageBlockTypeEnum,
    TutorialStatusEnum,
)
from apps.user.factories import UserFactory
from main.tests import TestCase
from utils.common import to_camel_case


class TestTutorialQuery(TestCase):
    class Query:
        TUTORIALS = """
            query Tutorials($pagination: OffsetPaginationInput) {
              tutorials(order: {id: ASC}, pagination: $pagination) {
                totalCount
                pageInfo {
                  offset
                  limit
                }
                results {
                  id
                  clientId
                  name
                  status
                  projectId
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
                    }
                  }
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
                }
              }
            }
        """

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

        cls.project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            requesting_organization=cls.organization,
            project_type=random.choice(list(ProjectTypeEnum)),  # noqa: S311
        )

        cls.tutorial = TutorialFactory.create(
            **cls.user_resource_kwargs,
            project=cls.project,
            name="Simple Tutorial",
            status=TutorialStatusEnum.PUBLISHED,
        )

        cls.scenario = TutorialScenarioPageFactory.create(
            **cls.user_resource_kwargs,
            tutorial=cls.tutorial,
            instructions_icon=IconEnum.ADD_OUTLINE,
            hint_icon=IconEnum.HELP_OUTLINE,
            success_icon=IconEnum.FLAG_OUTLINE,
        )

        cls.task = TutorialTaskFactory.create(
            **cls.user_resource_kwargs,
            scenario=cls.scenario,
            reference=1,
        )

        cls.info_page = TutorialInformationPageFactory.create(
            **cls.user_resource_kwargs,
            tutorial=cls.tutorial,
            title="Info Page",
            page_number=1,
        )

        cls.block = TutorialInformationPageBlockFactory.create(
            **cls.user_resource_kwargs,
            page=cls.info_page,
            block_type=random.choice(list(TutorialInformationPageBlockTypeEnum)),  # noqa: S311
        )

    def test_tutorials(self):
        def _query():
            return self.query_check(
                self.Query.TUTORIALS,
                variables={
                    "pagination": {
                        "limit": 10,
                        "offset": 0,
                    },
                },
            )

        # Without authentication -----
        content = _query()
        assert content["data"]["tutorials"] == {
            **self.g_pagination(offset=0, limit=10, total_count=0, results=[]),
        }, content

        # With authentication -----
        self.force_login(self.user)
        content = _query()
        assert content["data"]["tutorials"] == {
            **self.g_pagination(
                offset=0,
                limit=10,
                total_count=1,
                results=[
                    {
                        "id": self.gID(self.tutorial.pk),
                        "clientId": to_camel_case(self.tutorial.client_id),
                        "name": self.tutorial.name,
                        "status": self.tutorial.status.name,  # type: ignore[union-attr]
                        "projectId": self.gID(self.tutorial.project_id),
                        "scenarios": [
                            {
                                "id": self.gID(self.scenario.pk),
                                "clientId": to_camel_case(self.scenario.client_id),
                                "scenarioPageNumber": self.scenario.scenario_page_number,
                                "instructionsDescription": self.scenario.instructions_description,
                                "instructionsIcon": self.scenario.instructions_icon.name,  # type: ignore[union-attr]
                                "instructionsTitle": self.scenario.instructions_title,
                                "hintDescription": self.scenario.hint_description,
                                "hintIcon": self.scenario.hint_icon.name,  # type: ignore[union-attr]
                                "hintTitle": self.scenario.hint_title,
                                "successDescription": self.scenario.success_description,
                                "successIcon": self.scenario.success_icon.name,  # type: ignore[union-attr]
                                "successTitle": self.scenario.success_title,
                                "tasks": [
                                    {
                                        "id": self.gID(self.task.pk),
                                        "clientId": to_camel_case(self.task.client_id),
                                        "reference": self.task.reference,
                                    },
                                ],
                            },
                        ],
                        "informationPages": [
                            {
                                "id": self.gID(self.info_page.pk),
                                "clientId": to_camel_case(self.info_page.client_id),
                                "pageNumber": self.info_page.page_number,
                                "title": self.info_page.title,
                                "blocks": [
                                    {
                                        "id": self.gID(self.block.pk),
                                        "clientId": to_camel_case(self.block.client_id),
                                        "blockType": self.block.block_type.name,  # type: ignore[union-attr]
                                        "blockNumber": self.block.block_number,
                                        "text": self.block.text,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            ),
        }, content
