import typing

from django.core.exceptions import ValidationError
from django.http.request import HttpRequest
from django.utils.translation import gettext
from rest_framework import serializers

from apps.common.models import UserResource
from utils.common import validate_ulid


class DrfContextType(typing.TypedDict):
    request: HttpRequest


# FIXME(tnagorra): Add support for DrfContextType in __init__
# Reference: https://github.com/locustio/locust/blob/master/locust/clients.py#L144
class UserResourceSerializer[ModelType: UserResource, ContextType: DrfContextType = DrfContextType](
    serializers.ModelSerializer[ModelType],
):
    instance: ModelType | None  # type: ignore[override]

    @typing.override
    def get_fields(self):
        fields = super().get_fields()
        fields["client_id"] = serializers.CharField()
        return fields

    def validate_client_id(self, new_client_id: str | None):
        if new_client_id is None:
            return None

        try:
            validate_ulid(new_client_id)
            return new_client_id
        except ValidationError as err:
            raise serializers.ValidationError(
                gettext("Not a valid ULID value '%s'") % new_client_id,
            ) from err

    @property
    def context(self) -> ContextType:  # type: ignore[override]
        context = super().context
        assert context is not None, f"Always pass context when using {type(self)}"
        return typing.cast("ContextType", context)

    @typing.override
    def create(self, validated_data: dict[str, typing.Any]) -> ModelType:
        if "created_by" in self.Meta.model._meta._forward_fields_map:  # type: ignore[reportAttributeAccessIssue]
            validated_data["created_by"] = self.context["request"].user
        if "modified_by" in self.Meta.model._meta._forward_fields_map:  # type: ignore[reportAttributeAccessIssue]
            validated_data["modified_by"] = self.context["request"].user
        return super().create(validated_data)

    @typing.override
    def update(self, instance: ModelType, validated_data: dict[str, typing.Any]) -> ModelType:
        if "modified_by" in self.Meta.model._meta._forward_fields_map:  # type: ignore[reportAttributeAccessIssue]
            validated_data["modified_by"] = self.context["request"].user

        return super().update(instance, validated_data)
