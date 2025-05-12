# pyright: reportRedeclaration=false
# pyright: reportIncompatibleVariableOverride=false
# pyright: reportMissingTypeArgument=false
from factory.django import DjangoModelFactory

from .models import AggregatedUserGroupStatData, AggregatedUserStatData


class AggregatedUserStatDataFactory(DjangoModelFactory):
    class Meta:
        model = AggregatedUserStatData


class AggregatedUserGroupStatDataFactory(DjangoModelFactory):
    class Meta:
        model = AggregatedUserGroupStatData
