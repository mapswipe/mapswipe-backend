from apps.project.project_types.tile_map_service.compare import project as compare


# NOTE: If we want to extend these property, we will need to update CompletenesProject
class CompletenessProjectProperty(compare.CompareProjectProperty): ...


# NOTE: If we want to extend these property, we will need to update CompletenesProject
class CompletenessProjectTaskGroupProperty(compare.CompareProjectTaskGroupProperty): ...


# NOTE: If we want to extend these property, we will need to update CompletenesProject
class CompletenessProjectTaskProperty(compare.CompareProjectTaskProperty): ...


class CompletenessProject(
    compare.CompareProject,
): ...
