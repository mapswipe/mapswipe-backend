import datetime
import typing

from pydantic import BaseModel
from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import Project, ProjectStatusEnum, ProjectTypeEnum
from project_types.tile_map_service.base import project as tile_map_service_project
from utils.firebase import FbProject
from utils.geo.raster_tile_server.config import RasterTileServerNameEnum


# TODO(tnagora): Move this to firebase
# TODO(tnagora): Check if we need TypesyncUndefined for array and dictionary iterations
def serialize(obj: typing.Any):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize(i) for i in obj]
    if isinstance(obj, BaseModel):
        return serialize(obj.model_dump(mode="python"))
    return obj


# TODO(tnagorra): Move this somewhere more appropriate
def project_type_enum_to_firebase(input_enum: ProjectTypeEnum) -> firebase_models.FbEnumProjectType:
    match input_enum:
        case ProjectTypeEnum.FIND:
            return firebase_models.FbEnumProjectType.FIND
        case ProjectTypeEnum.COMPARE:
            return firebase_models.FbEnumProjectType.COMPARE
        case ProjectTypeEnum.COMPLETENESS:
            return firebase_models.FbEnumProjectType.COMPLETENESS
        case ProjectTypeEnum.VALIDATE:
            return firebase_models.FbEnumProjectType.VALIDATE
        case ProjectTypeEnum.VALIDATE_IMAGE:
            return firebase_models.FbEnumProjectType.VALIDATE_IMAGE


# TODO(tnagorra): Move this somewhere more appropriate
def raster_tile_server_name_enum_to_firebase(
    input_enum: RasterTileServerNameEnum,
) -> firebase_models.FbEnumRasterTileServerName:
    match input_enum:
        case RasterTileServerNameEnum.CUSTOM:
            return firebase_models.FbEnumRasterTileServerName.CUSTOM
        case RasterTileServerNameEnum.BING:
            return firebase_models.FbEnumRasterTileServerName.BING
        case RasterTileServerNameEnum.MAPBOX:
            return firebase_models.FbEnumRasterTileServerName.MAPBOX
        case RasterTileServerNameEnum.MAXAR_STANDARD:
            return firebase_models.FbEnumRasterTileServerName.MAXAR_STANDARD
        case RasterTileServerNameEnum.MAXAR_PREMIUM:
            return firebase_models.FbEnumRasterTileServerName.MAXAR_PREMIUM
        case RasterTileServerNameEnum.ESRI:
            return firebase_models.FbEnumRasterTileServerName.ESRI
        case RasterTileServerNameEnum.ESRI_BETA:
            return firebase_models.FbEnumRasterTileServerName.ESRI_BETA


class FindProjectProperty(tile_map_service_project.TileMapServiceProjectProperty): ...


class FindProjectTaskGroupProperty(tile_map_service_project.TileMapServiceProjectTaskGroupProperty): ...


class FindProjectTaskProperty(tile_map_service_project.TileMapServiceProjectTaskProperty): ...


class FindProject(
    tile_map_service_project.TileMapServiceBaseProject[
        FindProjectProperty,
        FindProjectTaskGroupProperty,
        FindProjectTaskProperty,
    ],
):
    project_property_class = FindProjectProperty
    project_task_group_property_class = FindProjectTaskGroupProperty
    project_task_property_class = FindProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)
        if typing.TYPE_CHECKING:
            assert project.project_type == ProjectTypeEnum.FIND, f"{type(self)} is defined for FIND"

    @typing.override
    def handle_new_project_on_firebase(self, project_ref):
        assert self.project.tutorial_id is not None
        assert self.project.image is not None

        tsp = self.project_type_specifics.tile_server_property

        # FIXME: If taskId is defined, should be private_inactive
        status = firebase_models.FbEnumProjectStatus.INACTIVE
        if self.project.status_enum == ProjectStatusEnum.PUBLISHED:
            # FIXME: If taskId is defined, should be private_active
            status = firebase_models.FbEnumProjectStatus.PRIVATE_ACTIVE

        project_ref.set(
            value=serialize(
                FbProject(
                    created=self.project.created_at,
                    createdBy=str(self.project.created_by_id),  # FIXME(tnagorra): user id or old id
                    # FIXME(tnagorra): We need to provide full url
                    # FIXME(tnagorra): Looks like this is required in model currently
                    image=self.project.image.file.url if self.project.image else firebase_models.UNDEFINED,
                    isFeatured=self.project.is_featured,
                    # FIXME(tnagorra): Need to check how we get this?
                    language="en-us",
                    lookFor=self.project.look_for,
                    # FIXME(tnagorra): This is not passed here
                    manualUrl=self.project.additional_info_url or firebase_models.UNDEFINED,
                    maxTasksPerUser=self.project.max_tasks_per_user or firebase_models.UNDEFINED,
                    groupMaxSize=self.project.group_size,  # this is zero
                    contributorCount=0,
                    progress=0,
                    resultCount=0,
                    groupSize=self.project.group_size,
                    projectId=str(self.project.id),  # FIXME(tnagorra): project id or old id
                    projectDetails=self.project.description,
                    name=self.project.name,
                    # FIXME(tnagorra): Fill these when implemented
                    projectNumber=1,  # numeric
                    projectRegion="",
                    projectTopic="",
                    projectTopicKey="",
                    projectType=project_type_enum_to_firebase(self.project.project_type_enum),
                    # project_type=project_type_enum_to_firebase(self.project.project_type_enum), # not needed here
                    requestingOrganisation=self.project.requesting_organization.name,  # str
                    # FIXME: need to calculate this
                    requiredResults=0,  # no. of results
                    status=status,
                    # FIXME(tnagorra): Fill this when implemented
                    teamId=firebase_models.UNDEFINED,
                    tutorialId=str(self.project.tutorial_id),  # FIXME(tnagorra): tutorial id or old id
                    verificationNumber=self.project.verification_number,
                    # NOTE: Project specific details
                    # FIXME(tnagorra): non project specific information should be handled outside
                    zoomLevel=self.project_type_specifics.zoom_level,
                    tileServer=firebase_models.FbObjRasterTileServer(
                        # FIXME(tnagorra): This name may be different, for bing it's bing
                        name=raster_tile_server_name_enum_to_firebase(tsp.name),
                        credits=tsp.get_credits(),
                        url=tsp.get_url(),
                        # NOTE: We already replace apiKey in the url so apiKey is empty
                        apiKey=firebase_models.UNDEFINED,
                        # NOTE: wmtsLayerName is deprecated as singergise is not longer supported
                        wmtsLayerName=firebase_models.UNDEFINED,
                    ),
                    tileServerB=firebase_models.UNDEFINED,
                ),
            ),
        )

        # TODO(tnagorra): Create groups
        # TODO(tnagorra): Create tasks (if necessary)

    @typing.override
    def handle_project_update_on_firebase(self, project_ref, fb_project):
        assert self.project.tutorial_id is not None

        status = fb_project.status
        if (
            status
            in [
                firebase_models.FbEnumProjectStatus.INACTIVE,
                firebase_models.FbEnumProjectStatus.PRIVATE_INACTIVE,
            ]
            and self.project.status_enum == ProjectStatusEnum.PUBLISHED
        ):
            # FIXME: If taskId is defined, should be private_active
            status = firebase_models.FbEnumProjectStatus.ACTIVE
        elif status in [
            firebase_models.FbEnumProjectStatus.ACTIVE,
            firebase_models.FbEnumProjectStatus.PRIVATE_ACTIVE,
        ] and self.project.status_enum in [ProjectStatusEnum.ARCHIVED, ProjectStatusEnum.PAUSED]:
            # FIXME: If taskId is defined, should be private_inactive
            status = firebase_models.FbEnumProjectStatus.INACTIVE

        project_ref.update(
            value=serialize(
                firebase_models.FbProjectUpdateInput(
                    image=self.project.image.file.url if self.project.image else firebase_models.UNDEFINED,
                    isFeatured=self.project.is_featured,
                    lookFor=self.project.look_for,
                    name=self.project.name,
                    # FIXME(tnagorra): Fill these when implemented
                    projectNumber=1,
                    projectRegion="",
                    projectTopic="",
                    projectTopicKey="",
                    projectDetails=self.project.description,
                    requestingOrganisation=self.project.requesting_organization.name,
                    tutorialId=str(self.project.tutorial_id),
                    status=status,
                    # FIXME(tnagorra): Fill this when implemented
                    teamId=firebase_models.UNDEFINED,
                    # FIXME(tnagorra): Need to check how we get this?
                    language="en-us",
                ),
            ),
        )
