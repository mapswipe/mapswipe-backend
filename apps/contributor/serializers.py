import typing

from django.utils import timezone

from apps.common.serializers import UserResourceSerializer

from .models import ContributorUserGroup


class ContributorUserGroupSerializer(UserResourceSerializer[ContributorUserGroup]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ContributorUserGroup
        fields = (
            "name",
            "description",
            "is_archived",
        )

    # FIXME(tnagorra): We should be able to make archivable models generic
    @typing.override
    def update(self, instance: ContributorUserGroup, validated_data: dict[str, typing.Any]) -> ContributorUserGroup:
        if validated_data["is_archived"] and not instance.is_archived:
            validated_data["archived_by"] = self.context["request"].user
            validated_data["archived_at"] = timezone.now()

        if not validated_data["is_archived"] and instance.is_archived:
            validated_data["archived_by"] = None
            validated_data["archived_at"] = None

        return super().update(instance, validated_data)
