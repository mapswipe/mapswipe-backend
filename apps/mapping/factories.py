# pyright: reportRedeclaration=false
# pyright: reportIncompatibleVariableOverride=false
# pyright: reportMissingTypeArgument=false
import typing

from factory.django import DjangoModelFactory

from .models import (
    MappingSession,
    MappingSessionClientTypeEnum,
    MappingSessionResult,
    MappingSessionUserGroup,
)


class MappingSessionFactory(DjangoModelFactory):
    class Meta:
        model = MappingSession

    app_version = "v1"
    client_type = MappingSessionClientTypeEnum.MOBILE_ANDROID


class MappingSessionUserGroupFactory(DjangoModelFactory):
    class Meta:
        model = MappingSessionUserGroup


class MappingSessionResultFactory(DjangoModelFactory):
    class Meta:
        model = MappingSessionResult


# NOTE: Make sure to add type hints for each factory class defined below
# NOTE: This needs to be at the end of this file
if typing.TYPE_CHECKING:
    MappingSessionFactory: type[DjangoModelFactory[MappingSession]]
    MappingSessionUserGroupFactory: type[DjangoModelFactory[MappingSessionUserGroup]]
    MappingSessionResultFactory: type[DjangoModelFactory[MappingSessionResult]]
