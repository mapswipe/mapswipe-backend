from django.db import models


# -- Helper
def load_model_objects[DjangoModel: models.Model](
    Model: type[DjangoModel],
    keys: list[int],
) -> list[DjangoModel]:
    qs = Model.objects.filter(id__in=keys)
    _map = {obj.pk: obj for obj in qs}
    return [_map[key] for key in keys]
