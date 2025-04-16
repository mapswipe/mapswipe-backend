import argparse
import typing

from django.core.management.base import BaseCommand, CommandParser
from strawberry.printer import print_schema

from main.graphql.schema import schema


class Command(BaseCommand):
    help = "Create schema.graphql file"

    @typing.override
    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--out",
            type=argparse.FileType("w"),
            default="schema.graphql",
        )

    @typing.override
    def handle(self, *args: typing.Any, **options: typing.Any):
        file = options["out"]
        file.write(print_schema(schema))
        file.close()
        self.stdout.write(self.style.SUCCESS(f"{file.name} file generated"))
