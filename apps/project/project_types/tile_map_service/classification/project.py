from apps.project.models import Project, ProjectTypeEnum

from ..base import project as tile_map_service_project


class ClassificationProjectProperty(tile_map_service_project.TileMapServiceProjectProperty): ...


class ClassificationProjectTaskGroupProperty(tile_map_service_project.TileMapServiceProjectTaskGroupProperty): ...


class ClassificationProjectTaskProperty(tile_map_service_project.TileMapServiceProjectTaskProperty): ...


class ClassificationProject(tile_map_service_project.TileMapServiceBaseProject):
    project_property_class = ClassificationProjectProperty
    project_task_group_property_class = ClassificationProjectTaskGroupProperty
    project_task_property_class = ClassificationProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)
        assert project.project_type == ProjectTypeEnum.BUILD_AREA, f"{type(self)} is defined for BUILD_AREA"
