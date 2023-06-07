import datetime
from enum import Enum
from functools import cache
from typing import Any, Literal, Optional, TypeVar, Union

import pydantic.main
from camel_converter import to_pascal
from icecream import ic
from neomodel import (
    BooleanProperty,
    DateProperty,
    DateTimeProperty,
    FloatProperty,
    IntegerProperty,
    One,
    OneOrMore,
    Property,
    RelationshipManager,
    StringProperty,
    UniqueIdProperty,
    ZeroOrMore,
    ZeroOrOne,
)
from pros_core.models import BaseNode
from pros_core.setup_utils.build_app_model_definitions import (
    build_child_nodes,
    build_properties,
    build_related_reifications,
    build_relationships,
    build_reverse_relationships,
    build_subclasses_set,
)
from pydantic import UUID4, BaseModel, Field, conlist, create_model

AnyItemType = TypeVar("AnyItemType")


def map_prop_and_default(neomodel_property):
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

    return prop, default


def build_pydantic_properties(
    neomodel_class: type[BaseNode],
) -> dict[str, tuple[type, Any]]:
    neomodel_properties = build_properties(neomodel_class)
    pydantic_properties = {}
    for neomodel_property_name, neomodel_property in neomodel_properties.items():
        if neomodel_property_name == "real_type":
            continue

        prop, default = map_prop_and_default(neomodel_property)

        pydantic_properties[neomodel_property_name] = (prop, default)

    return pydantic_properties


def get_existing_base_model_class(name):
    all_subclasses = BaseModel.__subclasses__()
    filtered_subclasses = [cls for cls in all_subclasses if cls.__name__ == name]
    if filtered_subclasses:
        return filtered_subclasses[0]
    return None


def build_relation_return_name(
    relationship_from_neomodel_class: type[BaseNode],
    relationship_name: str,
    relationship_to_neomodel_class: type[BaseNode],
):
    return f"{relationship_from_neomodel_class.__name__}_{to_pascal(relationship_name)}_{relationship_to_neomodel_class.__name__}_Related"


def build_relation_data_model(
    relation_properties: dict[str, Property], data_model_name
):
    pydantic_properties = {}
    for neomodel_property_name, neomodel_property in relation_properties.items():
        if neomodel_property_name == "real_type":
            continue

        prop, default = map_prop_and_default(neomodel_property)

        pydantic_properties[neomodel_property_name] = (prop, default)

    pydantic_model = create_model(
        f"{data_model_name}_RelationData",
        **pydantic_properties,
    )
    return pydantic_model


def build_relation_return_model(
    relationship_from_neomodel_class: type[BaseNode],
    relationship_name: str,
    relationship_to_neomodel_class: type[BaseNode],
    relation_properties: Optional[dict[str, Property]] = None,
    base=None,
) -> type[BaseModel]:
    class_name = build_relation_return_name(
        relationship_from_neomodel_class=relationship_from_neomodel_class,
        relationship_name=relationship_name,
        relationship_to_neomodel_class=relationship_to_neomodel_class,
    )
    if existing_pydantic_class := get_existing_base_model_class(class_name):
        return existing_pydantic_class

    additional_model_properties = {}

    if relation_properties:
        relation_property_model = build_relation_data_model(
            relation_properties, class_name
        )
        additional_model_properties["relation_data"] = (relation_property_model, ...)

    pydantic_model = create_model(
        class_name,
        __base__=base,
        real_type=(Literal[relationship_to_neomodel_class.__name__.lower()], relationship_to_neomodel_class.__name__.lower()),  # type: ignore
        label=(str, ...),
        uid=(UUID4, ...),
        **additional_model_properties,
    )
    return pydantic_model


def build_list_constraints_from_relation_manager(
    item_type: type[type],
    relationship_manager: RelationshipManager,
) -> type[list[AnyItemType]]:
    constraints = {"unique_items": True}
    if relationship_manager is One or relationship_manager is OneOrMore:
        constraints["min_items"] = 1
    if relationship_manager is One or relationship_manager is ZeroOrOne:
        constraints["max_items"] = 1

    cl = conlist(item_type, **constraints)

    return cl


def build_pydantic_return_relations(
    neomodel_class: type[BaseNode],
) -> dict[tuple[list[BaseModel], Any]]:
    """Build pydantic model for all relation types returned (not all fields, just uid + label)"""

    # Get all the relations
    neomodel_relations = build_relationships(neomodel_class)

    pydantic_relations = {}

    # Iterate relations
    for relationship_name, relation_app_model in neomodel_relations.items():
        # If relation is to a trait (not a standard node), look up all the standard node classes
        # that have this trait and return a Union type of them
        if relation_app_model.target_model.__is_trait__:
            pydantic_models_with_trait = [
                build_relation_return_model(
                    relationship_from_neomodel_class=neomodel_class,
                    relationship_name=relationship_name,
                    relationship_to_neomodel_class=cls,
                    relation_properties=relation_app_model.relation_properties,
                )
                for cls in relation_app_model.target_model.__classes_with_trait__
            ]

            pydantic_relations[relationship_name] = (
                build_list_constraints_from_relation_manager(
                    Union[*tuple(pydantic_models_with_trait)], relation_app_model.relation_manager  # type: ignore
                ),
                ...,
            )  # type: ignore

        # Otherwise, build the relation for the related node type
        else:
            # If a relationship is to a class, it can be related to any subtype!
            types = []

            # Get the return pydantic model for the base related model
            pydantic_base_model = build_relation_return_model(
                relationship_from_neomodel_class=neomodel_class,
                relationship_name=relationship_name,
                relationship_to_neomodel_class=relation_app_model.target_model,
                relation_properties=relation_app_model.relation_properties,
            )

            # If base model is not abstract, add its pydantic model to the possible types
            if not relation_app_model.target_model.is_abstract:
                types.append(pydantic_base_model)

            # Get all the subclasses and create a
            for subclass_app_model in build_subclasses_set(
                relation_app_model.target_model
            ):
                subclass_pydantic_model = build_relation_return_model(
                    relationship_from_neomodel_class=neomodel_class,
                    relationship_name=relationship_name,
                    relationship_to_neomodel_class=subclass_app_model.model,
                    relation_properties=relation_app_model.relation_properties,
                )
                types.append(subclass_pydantic_model)

            t_tuple = tuple(types)
            pydantic_relations[relationship_name] = (
                build_list_constraints_from_relation_manager(
                    Union[*t_tuple], relation_app_model.relation_manager  # type: ignore
                ),
                ...,
            )

    return pydantic_relations


def build_pydantic_return_related_reifications(
    neomodel_class: type[BaseNode],
) -> dict[tuple[list[BaseModel]], Any]:
    neomodel_abstract_reifications = build_related_reifications(neomodel_class)
    pydantic_relations = {}

    for (
        reification_name,
        reificiation_app_model,
    ) in neomodel_abstract_reifications.items():
        types = []

        if not reificiation_app_model.target_model.is_abstract:
            base_model = build_pydantic_model(reificiation_app_model.target_model)
            types.append(base_model)

        for subclass_app_model in build_subclasses_set(
            reificiation_app_model.target_model
        ):
            subclass_pydantic_model = build_pydantic_model(subclass_app_model.model)
            types.append(subclass_pydantic_model)

        t_tuple = tuple(types)
        pydantic_relations[reification_name] = (
            build_list_constraints_from_relation_manager(
                Union[*t_tuple], reificiation_app_model.relation_manager  # type: ignore
            ),
            ...,
        )


def build_pydantic_return_child_nodes(
    neomodel_class: type[BaseNode],
) -> dict[tuple[list[BaseModel], Any]]:
    """Build pydantic model for child nodes"""
    neomodel_child_nodes = build_child_nodes(neomodel_class)
    pydantic_properties = {}

    for relationship_name, relation_app_model in neomodel_child_nodes.items():
        types = []

        if not relation_app_model.child_model.is_abstract:
            base_model = build_pydantic_model(relation_app_model.child_model)
            types.append(base_model)

        for subclass_app_model in build_subclasses_set(relation_app_model.child_model):
            subclass_pydantic_model = build_pydantic_model(subclass_app_model.model)
            types.append(subclass_pydantic_model)

        t_tuple = tuple(types)
        pydantic_properties[relationship_name] = (
            build_list_constraints_from_relation_manager(
                Union[*t_tuple], relation_app_model.relation_manager  # type: ignore
            ),
            ...,
        )

    return pydantic_properties


def build_pydantic_return_reverse_relations(
    neomodel_class: type[BaseNode],
) -> type[BaseModel]:
    neomodel_reverse_relation_nodes = build_reverse_relationships(neomodel_class)
    pydantic_relations = {}
    for (
        reverse_relation_name,
        reverse_relation_app_model,
    ) in neomodel_reverse_relation_nodes.items():
        types = []
        if reverse_relation_app_model.relationship_from_model.__is_trait__:
            pydantic_models_with_trait = [
                build_relation_return_model(
                    relationship_from_neomodel_class=cls,
                    relationship_name=reverse_relation_app_model.forward_relationship_label,
                    relationship_to_neomodel_class=neomodel_class,
                )
                for cls in reverse_relation_app_model.relationship_from_model.__classes_with_trait__
            ]

            pydantic_relations[reverse_relation_name] = (
                Optional[list[Union[*tuple(pydantic_models_with_trait)]]],  # type: ignore
                None,
            )

        else:
            if not reverse_relation_app_model.relationship_from_model.is_abstract:
                base_model = build_relation_return_model(
                    relationship_from_neomodel_class=reverse_relation_app_model.relationship_from_model,
                    relationship_name=reverse_relation_app_model.forward_relationship_label,
                    relationship_to_neomodel_class=neomodel_class,
                )
                types.append(base_model)

            for subclass_app_model in build_subclasses_set(
                reverse_relation_app_model.relationship_from_model
            ):
                subclass_pydantic_model = build_relation_return_model(
                    relationship_from_neomodel_class=subclass_app_model.model,
                    relationship_name=reverse_relation_app_model.forward_relationship_label,
                    relationship_to_neomodel_class=neomodel_class,
                )
                types.append(subclass_pydantic_model)

            t_tuple = tuple(types)
            t = list[Union[*t_tuple]]  # type: ignore
            pydantic_relations[reverse_relation_name] = (
                Optional[t],
                None,
            )

    return pydantic_relations


def build_pydantic_model(neomodel_class: type[BaseNode]) -> type[BaseModel]:
    """Build a standard pydantic model (all fields, rels)"""
    if existing_pydantic_model := get_existing_base_model_class(neomodel_class):
        return existing_pydantic_model

    pydantic_properties = build_pydantic_properties(neomodel_class)
    pydantic_relations = build_pydantic_return_relations(neomodel_class)
    pydantic_child_nodes = build_pydantic_return_child_nodes(neomodel_class)
    pydantic_reverse_relations = build_pydantic_return_reverse_relations(neomodel_class)

    pydantic_model = create_model(
        neomodel_class.__name__,
        real_type=(
            Literal[neomodel_class.__name__.lower()],  # type: ignore
            neomodel_class.__name__.lower(),
        ),
        **pydantic_properties,
        **pydantic_relations,
        **pydantic_child_nodes,
        **pydantic_reverse_relations,
    )
    return pydantic_model


def build_pydantic_return_model(neomodel_class: type[BaseNode]) -> type[BaseModel]:
    """Build pydantic model for return types from DB/API"""

    model = build_pydantic_model(neomodel_class)

    # ic(Model.schema())
    return model
