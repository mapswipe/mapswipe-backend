from apps.project.models import Project, ProjectTypeEnum

from ..base.project import TileMapServiceBaseProject


class ClassificationProject(TileMapServiceBaseProject):
    def __init__(self, project: Project):
        super().__init__(project)
        assert project.project_type == ProjectTypeEnum.BUILD_AREA, f"{type(self)} is defined for BUILD_AREA"
