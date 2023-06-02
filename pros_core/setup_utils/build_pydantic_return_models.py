import datetime
from enum import Enum
from typing import Any, Optional, TypeVar, Union

import pydantic
from neomodel import (
    BooleanProperty,
    DateProperty,
    DateTimeProperty,
    FloatProperty,
    IntegerProperty,
    StringProperty,
    UniqueIdProperty,
)
from pros_core.models import BaseNode
from pros_core.setup_utils.build_app_model_definitions import (
    build_child_nodes,
    build_properties,
    build_relationships,
    build_subclasses_set,
)
from pydantic import UUID4, BaseModel, Field, create_model


def build_pydantic_properties(
    neomodel_class: type[BaseNode],
) -> dict[str, tuple[type, Any]]:
    neomodel_properties = build_properties(neomodel_class)
    pydantic_properties = {}
    for neomodel_property_name, neomodel_property in neomodel_properties.items():
        if neomodel_property_name == "real_type":
            continue

        if isinstance(neomodel_property, StringProperty):
            prop = str

        elif isinstance(neomodel_property, BooleanProperty):
            prop = bool

        elif isinstance(neomodel_property, DateProperty):
            prop = datetime.date

        elif isinstance(neomodel_property, DateTimeProperty):
            prop = datetime.datetime

        elif isinstance(neomodel_property, FloatProperty):
            prop = float

        elif isinstance(neomodel_property, IntegerProperty):
            prop = int

        elif isinstance(neomodel_property, UniqueIdProperty):
            prop = UUID4

        if neomodel_property.required != True:
            prop = Optional[prop]

        if not callable(neomodel_property.default):
            default = neomodel_property.default
        else:
            default = ...

        pydantic_properties[neomodel_property_name] = (prop, default)

    return pydantic_properties


def build_relation_return_model(neomodel_class: type[BaseNode], base=None):
    Model = create_model(
        f"{neomodel_class.__name__}",
        __base__=base,
        real_type=(Any, neomodel_class.__name__.lower()),
        label=(str, ...),
        uid=(UUID4, ...),
        relation_data=(dict, ...),
    )
    return Model


def build_pydantic_return_relations(
    neomodel_class: type[BaseNode],
) -> dict[tuple[list[BaseModel], Any]]:
    neomodel_relations = build_relationships(neomodel_class)
    pydantic_properties = {}

    for relationship_name, relationship in neomodel_relations.items():
        related_pydantic_model = build_relation_return_model(relationship.target_model)

        pydantic_properties[relationship_name] = (list[related_pydantic_model], ...)

    return pydantic_properties


def build_pydantic_return_child_nodes(
    neomodel_class: type[BaseNode],
) -> dict[tuple[list[BaseModel], Any]]:
    neomodel_child_nodes = build_child_nodes(neomodel_class)
    pydantic_properties = {}

    for relationship_name, relation_app_model in neomodel_child_nodes.items():
        # TODO: get subtypes with discriminator...
        types = []
        if not getattr(relation_app_model.child_model, "__abstract__", False):
            base_model = build_relation_return_model(relation_app_model.child_model)
            types.append(base_model)
        else:
            pydantic_properties = build_pydantic_properties(
                relation_app_model.child_model
            )
            pydantic_relations = build_pydantic_return_relations(
                relation_app_model.child_model
            )
            pydantic_child_nodes = build_pydantic_return_child_nodes(
                relation_app_model.child_model
            )

            base_model = create_model(
                relation_app_model.child_model.__name__,
                **pydantic_properties,
                **pydantic_relations,
                **pydantic_child_nodes,
            )

        for subclass_app_model in build_subclasses_set(relation_app_model.child_model):
            types.append(build_relation_return_model(subclass_app_model.model))

        t_tuple = tuple(types)
        pydantic_properties[relationship_name] = (
            list[Union[*t_tuple]],  # type: ignore
            ...,
        )
        print(pydantic_properties)

    return pydantic_properties


def build_pydantic_return_model(neomodel_class: type[BaseNode]) -> type[BaseModel]:
    RealTypeLiteral = Enum(  # type: ignore[misc]
        "RealType",
        (("val", neomodel_class.__name__.lower()),),
        type=str,
    )
    pydantic_properties = build_pydantic_properties(neomodel_class)
    pydantic_relations = build_pydantic_return_relations(neomodel_class)
    pydantic_child_nodes = build_pydantic_return_child_nodes(neomodel_class)
    Model = create_model(
        f"{neomodel_class.__name__}",
        real_type=(RealTypeLiteral, RealTypeLiteral.val.lower()),
        **pydantic_properties,
        **pydantic_relations,
        **pydantic_child_nodes,
    )
    print(Model.schema())

    return Model
