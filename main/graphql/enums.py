import dataclasses
from enum import Enum

import strawberry

from apps.contributor import models as contributor_enums
from apps.mapping import models as mapping_enums
from apps.project import models as project_enums
from apps.tutorial import models as tutorial_enums
from utils.geo.tile_server.config import TileServerNameEnum


@strawberry.enum
class DummyEnum(Enum):
    VALUE_1 = "Value 1"
    VALUE_2 = "Value 2"


ENUM_TO_STRAWBERRY_ENUMS: list[type] = [
    DummyEnum,
    TileServerNameEnum,
    project_enums.ProjectTypeEnum,
    project_enums.ProjectStatusEnum,
    tutorial_enums.TutorialInformationPageBlockTypeEnum,
    mapping_enums.MappingSessionClientTypeEnum,
    contributor_enums.ContributorUserGroupMembershipLogActionEnum,
]


class AppEnumData:
    def __init__(self, enum):
        self.enum = enum

    @property
    def key(self):
        return self.enum

    @property
    def label(self):
        return str(self.enum.label)


def generate_app_enum_collection_data(name: str):
    return type(
        name,
        (),
        {
            enum.__name__: [AppEnumData(e) for e in enum]  # type: ignore[reportGeneralTypeIssues]
            for enum in ENUM_TO_STRAWBERRY_ENUMS
        },
    )


AppEnumCollectionData = generate_app_enum_collection_data("AppEnumCollectionData")


def generate_type_for_enum(name: str, Enum):
    return strawberry.type(
        dataclasses.make_dataclass(
            f"AppEnumCollection{name}",
            [
                ("key", Enum),
                ("label", str),
            ],
        ),
    )


def _enum_type(name: str, Enum):
    EnumType = generate_type_for_enum(name, Enum)

    @strawberry.field
    def _field() -> list[EnumType]:  # type: ignore[reportGeneralTypeIssues]
        return [
            EnumType(
                key=e,
                label=e.label,
            )
            for e in Enum
        ]

    return list[EnumType], _field


def generate_type_for_enums():
    enum_fields = [
        (
            enum.__name__,
            *_enum_type(enum.__name__, enum),
        )
        for enum in ENUM_TO_STRAWBERRY_ENUMS
    ]
    return strawberry.type(
        dataclasses.make_dataclass(
            "AppEnumCollection",
            enum_fields,
        ),
    )


AppEnumCollection = generate_type_for_enums()
