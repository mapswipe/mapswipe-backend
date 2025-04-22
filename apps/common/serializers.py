import typing

from rest_framework import serializers

from apps.common.models import UserResource

ModelType = typing.TypeVar("ModelType", bound=UserResource)


class UserResourceSerializer(serializers.ModelSerializer[ModelType]):
    modified_at = serializers.DateTimeField(read_only=True)
    modified_by = serializers.PrimaryKeyRelatedField(read_only=True)

    instance: ModelType | None  # type: ignore[override]

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
