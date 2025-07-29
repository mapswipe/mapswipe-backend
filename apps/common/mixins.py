import mimetypes
import typing

from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext
from rest_framework import serializers

from apps.project.models import ProjectAsset
from apps.tutorial.models import TutorialAsset

if typing.TYPE_CHECKING:
    from django.core.files.base import ContentFile

AssetModel = TutorialAsset | ProjectAsset


class CommonAssetMixin:
    if typing.TYPE_CHECKING:

        class Meta:
            model: type[AssetModel]

        def validate(self, attrs: dict[str, typing.Any]) -> dict[str, typing.Any]: ...

    @property
    def model_class(self) -> type[AssetModel]:
        return self.Meta.model

    def _validate_file(self, attrs: dict[str, typing.Any]) -> None:
        file_content: ContentFile[bytes] = attrs["file"]
        file_size: int = file_content.size
        max_file_size = self.model_class.MAX_FILE_SIZE

        if file_size > max_file_size:
            raise serializers.ValidationError(
                gettext("Filesize should be less than: %s. Current is: %s")
                % (
                    filesizeformat(max_file_size),
                    filesizeformat(file_size),
                ),
            )

        # https://docs.python.org/3/library/mimetypes.html#mimetypes.guess_type
        mimetype, *_ = mimetypes.guess_type(file_content.name)  # type: ignore[reportUnknownArgumentType]

        # TODO(susilnem): Use library like filemagic to determine mimetype instead?
        if mimetype is None:
            raise serializers.ValidationError(
                gettext("Could not determine mimetype of the file: %s") % file_content.name,
            )

        if not self.model_class.Mimetype.is_valid_mimetype(mimetype):
            raise serializers.ValidationError(
                gettext("File mimetype is not supported: %s") % mimetype,
            )

        if "mimetype" in attrs and self.model_class.Mimetype.get_mimetype_by_label(mimetype) != attrs["mimetype"]:
            raise serializers.ValidationError(
                gettext("File mimetype does not match the provided mimetype: %s") % mimetype,
            )

        attrs["mimetype"] = self.model_class.Mimetype.get_mimetype_by_label(mimetype)
        attrs["file_size"] = file_size

    def validate(self, attrs: dict[str, typing.Any]) -> dict[str, typing.Any]:
        self._validate_file(attrs)
        return super().validate(attrs)  # type: ignore[misc]
