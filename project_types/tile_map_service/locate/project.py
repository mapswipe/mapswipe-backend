import typing

from django.db import models
from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import Project, ProjectTypeEnum
from project_types.tile_map_service.base import project as tile_map_service_project
from utils.custom_options.models import CustomOption


class SubGridSizeEnum(models.TextChoices):
    SIZE_2X2 = "2x2", "2x2"
    SIZE_4X4 = "4x4", "4x4"
    SIZE_8X8 = "8x8", "8x8"

    def to_firebase(self) -> firebase_models.FBEnumSubGridSize:
        match self:
            case SubGridSizeEnum.SIZE_2X2:
                return firebase_models.FBEnumSubGridSize.SIZE_2X2
            case SubGridSizeEnum.SIZE_4X4:
                return firebase_models.FBEnumSubGridSize.SIZE_4X4
            case SubGridSizeEnum.SIZE_8X8:
                return firebase_models.FBEnumSubGridSize.SIZE_8X8


class LocateProjectProperty(tile_map_service_project.TileMapServiceProjectProperty):
    sub_grid_size: SubGridSizeEnum
    custom_options: list[CustomOption] | None = None
    # NOTE: Additional export metadata. Example: {"building": "roof_top"}
    export_meta_key: str
    export_meta_value: str


class LocateProjectTaskGroupProperty(tile_map_service_project.TileMapServiceProjectTaskGroupProperty): ...


class LocateProjectTaskProperty(tile_map_service_project.TileMapServiceProjectTaskProperty): ...


class LocateProject(
    tile_map_service_project.TileMapServiceBaseProject[
        LocateProjectProperty,
        LocateProjectTaskGroupProperty,
        LocateProjectTaskProperty,
    ],
):
    project_property_class = LocateProjectProperty
    project_task_group_property_class = LocateProjectTaskGroupProperty
    project_task_property_class = LocateProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)
        if typing.TYPE_CHECKING:
            assert project.project_type == ProjectTypeEnum.LOCATE, f"{type(self)} is defined for LOCATE"

    @typing.override
    def get_max_time_spend_percentile(self) -> float:
        # TODO(susilnem): We might need to adjust this number later.
        return 1.4

    @typing.override
    def get_task_specifics_for_db(self, tile_x: int, tile_y: int) -> LocateProjectTaskProperty:
        return self.project_task_property_class(
            tile_x=tile_x,
            tile_y=tile_y,
            url=self.project_type_specifics.tile_server_property.generate_url(
                tile_x,
                tile_y,
                self.project_type_specifics.zoom_level,
            ),
        )

    # FIREBASE

    @typing.override
    def get_project_specifics_for_firebase(self):
        tsp = self.project_type_specifics.tile_server_property
        custom_opts = self.project_type_specifics.custom_options
        return firebase_models.FbProjectLocateCreateOnlyInput(
            zoomLevel=self.project_type_specifics.zoom_level,
            subGridSize=self.project_type_specifics.sub_grid_size.to_firebase(),
            exportMetaKey=self.project_type_specifics.export_meta_key,
            exportMetaValue=self.project_type_specifics.export_meta_value,
            tileServer=firebase_models.FbObjRasterTileServer(
                name=tsp.name.to_firebase(),
                credits=tsp.get_config()["credits"],
                url=tsp.get_config()["raw_url"],
                apiKey=tsp.get_config()["api_key"],
                wmtsLayerName=None,
            ),
            customOptions=[
                firebase_models.FbObjCustomOption(
                    title=opt.title,
                    description=opt.description,
                    value=opt.value,
                    icon=str(opt.icon.label),
                    iconColor=opt.icon_color,
                    subOptions=[
                        firebase_models.FbBaseObjCustomSubOption(
                            value=sub_opt.value,
                            description=sub_opt.description,
                        )
                        for sub_opt in opt.sub_options
                    ]
                    if opt.sub_options is not None
                    else None,
                )
                for opt in custom_opts
            ]
            if custom_opts is not None
            else None,
        )
