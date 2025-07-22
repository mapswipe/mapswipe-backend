from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import ProjectTypeEnum
from utils.geo.raster_tile_server.config import RasterTileServerNameEnum
from utils.geo.vector_tile_server.config import VectorTileServerNameEnum


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


def vector_tile_server_name_enum_to_firebase(
    input_enum: VectorTileServerNameEnum,
) -> firebase_models.FbEnumVectorTileServerName:
    match input_enum:
        case VectorTileServerNameEnum.CUSTOM:
            return firebase_models.FbEnumVectorTileServerName.CUSTOM
        case VectorTileServerNameEnum.OPEN_STREET_MAP:
            return firebase_models.FbEnumVectorTileServerName.OPEN_STREET_MAP
        case VectorTileServerNameEnum.OPEN_FREE_MAP:
            return firebase_models.FbEnumVectorTileServerName.OPEN_FREE_MAP
        case VectorTileServerNameEnum.VERSATILES:
            return firebase_models.FbEnumVectorTileServerName.VERSATILES
