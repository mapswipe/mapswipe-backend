from apps.common.serializers import ArchivableResourceSerializer, UserResourceSerializer

from .models import ContributorUserGroup


class ContributorUserGroupSerializer(
    UserResourceSerializer[ContributorUserGroup],
    ArchivableResourceSerializer[ContributorUserGroup],
):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ContributorUserGroup
        fields = (
            "name",
            "description",
            "is_archived",
        )
