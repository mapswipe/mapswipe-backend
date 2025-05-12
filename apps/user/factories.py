# pyright: reportRedeclaration=false
# pyright: reportIncompatibleVariableOverride=false
# pyright: reportMissingTypeArgument=false
import typing

import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from .models import User


class UserFactory(DjangoModelFactory):
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Sequence(lambda n: f"{n}@xyz.com")

    class Meta:
        model = User

    @factory.post_generation
    def password(
        obj: User,  # type: ignore[reportGeneralTypeIssues]
        create: bool,
        password: str,
        **_,
    ):
        if not create:
            return
        password_text = password or fuzzy.FuzzyText(length=15).fuzz()
        obj.set_password(password_text)
        obj.password_text = password_text  # type: ignore[reportUninitializedInstanceVariable]
        obj.save()  # type: ignore[reportAttributeAccessIssue]


# NOTE: Make sure to add type hints for each factory class defined below
# NOTE: This needs to be at the end of this file
if typing.TYPE_CHECKING:
    UserFactory: type[DjangoModelFactory[User]]
