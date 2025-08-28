import typing

from graphql import GraphQLEnumType, GraphQLObjectType, GraphQLUnionType
from graphql.utilities.print_schema import (
    print_block,
    print_deprecated,
    print_description,
)
from strawberry.printer import printer as sp
from strawberry.schema import BaseSchema
from strawberry.schema.schema_converter import GraphQLCoreConverter

# NOTE: We are sorting members in type, input, enums and unions
# The patch was created with reference to this file:
# https://github.com/strawberry-graphql/strawberry/blob/0.278.0/strawberry/printer/printer.py


def print_fields(
    type_: GraphQLObjectType,
    schema: BaseSchema,
    *,
    extras: sp.PrintExtras,
) -> str:
    fields = []

    for i, (name, field) in enumerate(sorted(type_.fields.items())):  # changed
        strawberry_field = field.extensions and field.extensions.get(
            GraphQLCoreConverter.DEFINITION_BACKREF,
        )

        args = sp.print_args(field.args, "  ", schema=schema, extras=extras) if hasattr(field, "args") else ""

        fields.append(
            print_description(field, "  ", not i)
            + f"  {name}"
            + args
            + f": {field.type}"
            + sp.print_field_directives(strawberry_field, schema=schema, extras=extras)
            + print_deprecated(field.deprecation_reason),
        )

    return print_block(fields)


def print_enum(
    type_: GraphQLEnumType,
    *,
    schema: BaseSchema,
    extras: sp.PrintExtras,
) -> str:
    strawberry_type = type_.extensions.get("strawberry-definition")
    directives = strawberry_type.directives if strawberry_type else []

    printed_directives = "".join(
        sp.print_schema_directive(directive, schema=schema, extras=extras) for directive in directives
    )

    values = [
        sp.print_enum_value(name, value, not i, schema=schema, extras=extras)
        for i, (name, value) in enumerate(sorted(type_.values.items()))  # changed
    ]
    return print_description(type_) + f"enum {type_.name}" + printed_directives + print_block(values)


def _print_input_object(type_: typing.Any, schema: BaseSchema, *, extras: sp.PrintExtras) -> str:
    fields = []
    for i, (name, field) in enumerate(sorted(type_.fields.items())):  # changed
        strawberry_field = field.extensions and field.extensions.get(
            GraphQLCoreConverter.DEFINITION_BACKREF,
        )

        fields.append(
            print_description(field, "  ", not i)
            + "  "
            + sp.print_input_value(name, field)
            + sp.print_field_directives(strawberry_field, schema=schema, extras=extras),
        )

    return (
        print_description(type_)
        + f"input {type_.name}"
        + sp.print_type_directives(type_, schema, extras=extras)
        + print_block(fields)
    )


def print_union(
    type_: GraphQLUnionType,
    *,
    schema: BaseSchema,
    extras: sp.PrintExtras,
) -> str:
    strawberry_type = type_.extensions.get("strawberry-definition")
    directives = strawberry_type.directives if strawberry_type else []

    printed_directives = "".join(
        sp.print_schema_directive(directive, schema=schema, extras=extras) for directive in directives
    )

    types = type_.types
    possible_types = " = " + " | ".join(sorted([t.name for t in types])) if types else ""  # changed
    return print_description(type_) + f"union {type_.name}{printed_directives}" + possible_types


sp.print_fields = print_fields
sp.print_enum = print_enum
sp._print_input_object = _print_input_object  # type: ignore[reportPrivateUsage]
sp.print_union = print_union
