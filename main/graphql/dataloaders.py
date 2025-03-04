from django.utils.functional import cached_property

# from apps.expale.dataloaders import ExampleDataLoader


# TODO: Use optimizer instead?
class GlobalDataLoader:
    @cached_property
    def user(self):
        ...
        # return ExampleDataLoader()
