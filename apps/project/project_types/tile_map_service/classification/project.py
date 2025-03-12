from apps.project.models import Project, ProjectType

from ..base.project import TileMapServiceBaseProject


class ClassificationProject(TileMapServiceBaseProject):
    def __init__(self, project: Project):
        super().__init__(project)
        assert project.project_type == ProjectType.BUILD_AREA, f"{type(self)} is defined for BUILD_AREA"
