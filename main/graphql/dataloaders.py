from django.utils.functional import cached_property

from apps.project.graphql.dataloaders import ProjectDataLoader


class GlobalDataLoader:
    @cached_property
    def project(self):
        return ProjectDataLoader()
