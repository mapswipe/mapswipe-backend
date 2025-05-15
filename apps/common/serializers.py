import typing

from django.http.request import HttpRequest
from django.utils.translation import gettext
from rest_framework import serializers
from ulid import ULID

from apps.common.models import UserResource


class DrfContextType(typing.TypedDict):
    request: HttpRequest


# FIXME(tnagorra): Add support for DrfContextType in __init__
# Reference: https://github.com/locustio/locust/blob/master/locust/clients.py#L144
class UserResourceSerializer[ModelType: UserResource, ContextType: DrfContextType = DrfContextType](
    serializers.ModelSerializer[ModelType],
):
    modified_at = serializers.DateTimeField(read_only=True)
    modified_by = serializers.PrimaryKeyRelatedField(read_only=True)
    client_id = serializers.CharField()

    instance: ModelType | None  # type: ignore[override]

    def validate_client_id(self, new_client_id: str):
        try:
            ULID.from_str(new_client_id)
            return new_client_id
        except (ValueError, TypeError) as err:
            raise serializers.ValidationError(
                gettext("Not a valid ULID value '%s'") % (new_client_id),
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
