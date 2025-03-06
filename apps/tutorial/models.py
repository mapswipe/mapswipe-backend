from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext, gettext_lazy
from django_choices_field import IntegerChoicesField

from apps.common.models import UserResource
from apps.project.models import Project


class UploadHelper:
    @staticmethod
    def information_page_block_image(instance: "TutorialInformationPageBlock", filename):
        return "tutorial/{0}/block-image/{1}".format(instance.page.tutorial_id, filename)


class Tutorial(UserResource):
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name="+",
        help_text=gettext_lazy("Project this tutorial is referring to."),
    )
    is_draft = models.BooleanField(default=True, help_text=gettext_lazy("Draft tutorial can be modified"))

    # TODO: Scenario Pages

    # Type hints
    project_id: int


class TutorialInformationPage(models.Model):
    tutorial: Tutorial = models.ForeignKey(  # type: ignore[reportAssignmentType]
        Tutorial,
        on_delete=models.CASCADE,
        related_name="+",
    )
    title = models.CharField(max_length=255)
    page_number = models.PositiveSmallIntegerField()

    # Type hints
    tutorial_id: int


class TutorialInformationPageBlockType(models.IntegerChoices):
    TEXT = 1, "Text"
    IMAGE = 2, "Image"


class TutorialInformationPageBlock(models.Model):
    Type = TutorialInformationPageBlockType

    page: TutorialInformationPage = models.ForeignKey(  # type: ignore[reportAssignmentType]
        TutorialInformationPage,
        on_delete=models.CASCADE,
        related_name="+",
    )

    block_number = models.PositiveSmallIntegerField()
    block_type = IntegerChoicesField(choices_enum=TutorialInformationPageBlockType)
    text = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to=UploadHelper.information_page_block_image, null=True, blank=True)

    # Type hints
    page_id: int

    def clean(self):
        if self.block_type == TutorialInformationPageBlockType.TEXT and (self.text is None or self.text == ""):
            raise ValidationError(gettext("Text should be provided for text block"))
        elif self.block_type == TutorialInformationPageBlockType.IMAGE and self.image.name is None:
            raise ValidationError(gettext("Image should be provided for image block"))
