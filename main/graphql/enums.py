import dataclasses

import strawberry

from apps.common import models as common_models
from apps.contributor import models as contributor_models
from apps.mapping import models as mapping_models
from apps.project import models as project_models
from apps.tutorial import models as tutorial_models
from project_types.tile_map_service.completeness.project import OverlayLayerTypeEnum
from project_types.validate.project import ValidateObjectSourceTypeEnum
from project_types.validate_image.project import ValidateImageSourceTypeEnum
from utils.geo.raster_tile_server.config import RasterTileServerNameEnum
from utils.geo.vector_tile_server.config import VectorTileServerNameEnum

ENUM_TO_STRAWBERRY_ENUMS: list[type] = [
    RasterTileServerNameEnum,
    VectorTileServerNameEnum,
    ValidateObjectSourceTypeEnum,
    ValidateImageSourceTypeEnum,
    OverlayLayerTypeEnum,
    project_models.ProjectTypeEnum,
    project_models.ProjectStatusEnum,
    project_models.ProjectProcessingStatusEnum,
    project_models.ProjectAssetInputTypeEnum,
    project_models.ProjectAssetExportTypeEnum,
    common_models.IconEnum,
    common_models.AssetMimetypeEnum,
    common_models.AssetTypeEnum,
    tutorial_models.TutorialStatusEnum,
    tutorial_models.TutorialInformationPageBlockTypeEnum,
    tutorial_models.TutorialAssetInputTypeEnum,
    mapping_models.MappingSessionClientTypeEnum,
    contributor_models.ContributorUserGroupMembershipLogActionEnum,
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
