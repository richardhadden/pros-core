from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Self

from camel_converter import to_pascal
from dotted_dict import DottedDict
from neomodel import (
    Property,
    RelationshipDefinition,
    RelationshipManager,
    UniqueIdProperty,
)
from ordered_set import OrderedSet
from pros_core.models import (
    REVERSE_RELATIONS,
    AbstractNode,
    AbstractReificationRelation,
    BaseNode,
    ChildNodeRelation,
)
from pydantic import BaseModel


@dataclass
class AppModelItem:
    model_name: str
    model: type[AbstractNode]
    app_name: str

    def __eq__(self, obj) -> bool:
        return self.model_name == obj

    def __hash__(self) -> int:
        return hash(self.model_name)

    def repr(self):
        return f"<HashedAppModelItem model_name='{self.model_name}' model={repr(self.model)} app_name='{self.app_name}'>"


@dataclass
class SubclassHierarchyItem:
    app_name: str
    model_name: str
    model: type[AbstractNode]
    subclasses: AppModelItem[Self]

    def __eq__(self, obj) -> bool:
        return self.model_name == obj

    def __hash__(self) -> int:
        return hash(self.model_name)


class AppModelSet(OrderedSet):
    def __getitem__(self, item) -> AppModel:
        return ModelManager(item)

    def __contains__(self, obj: str | type[AbstractNode]) -> bool:
        if isinstance(obj, str):
            obj = to_pascal(obj)
            return super().__contains__(obj)
        else:
            return super().__contains__(obj.__name__)

    def __repr__(self):
        return f"<{__class__.__name__} {', '.join(repr(item) for item in self)}>"


@dataclass
class RelationshipType:
    target_model_name: str
    relation_model: type[RelationshipDefinition]
    relation_label: str
    relation_manager: type[RelationshipManager]
    inline_createable: bool = False
    has_relation_data: bool = False
    relation_properties: list[str] = list

    @property
    def target_app_model(self) -> AppModel:
        return ModelManager.get_model(self.target_model_name)

    @property
    def target_model(self) -> type[AbstractNode]:
        return ModelManager.get_model(self.target_model_name).model_class


@dataclass
class ChildNodeRelationType:
    child_model_name: str
    relation_label: str
    relation_manager: type[RelationshipManager]

    @property
    def child_app_model(self):
        return ModelManager.get_model(self.child_model_name)

    @property
    def child_model(self):
        return ModelManager.get_model(self.child_model_name).model_class


@dataclass
class ReificationRelationshipType:
    target_model_name: str
    relation_model: type[RelationshipDefinition]
    relation_label: str
    relation_manager: type[RelationshipManager]

    @property
    def target_app_model(self) -> AppModel:
        return ModelManager.get_model(self.target_model_name)

    @property
    def target_model(self) -> type[AbstractNode]:
        return ModelManager.get_model(self.target_model_name).model_class


@dataclass
class AppModel:
    app_name: str
    model_class: BaseNode
    model_name: str
    _mm: ModelManagerClass
    meta: dict
    properties: dict
    relationships: dict[str, RelationshipType]
    child_nodes: dict[str, ChildNodeRelationType]
    related_reifications: dict[str, ReificationRelationshipType]
    subclass_hierarchy: AppModelItem[SubclassHierarchyItem]
    subclasses: AppModelSet[AppModelItem]
    parent_classes: AppModelSet[AppModelItem]
    reverse_relationships: dict[str, dict]
    pydantic_return_model: type[BaseModel] = None


class ModelManagerException(Exception):
    pass


class ModelManagerClass:
    def __init__(self):
        self.pros_models_by_app_name_model_name = {}
        self.pros_models_by_model_name = {}
        self.pros_models_by_model_class = {}

    def add_model(self, app_model: AppModel) -> None:
        """Adds an AppModel to the ModelManager"""
        self.pros_models_by_app_name_model_name[
            f"{to_pascal(app_model.app_name).lower()}.{to_pascal(app_model.model_name).lower()}"
        ] = app_model
        self.pros_models_by_model_name[
            to_pascal(app_model.model_name).lower()
        ] = app_model
        self.pros_models_by_model_class[app_model.model_class] = app_model

    def get_model(self, model_identifier: BaseNode | str) -> AppModel:
        """Get an AppModel by model class, qualified name ('<AppName>.<ModelName>'), or unqualified name"""

        # Get by class
        if inspect.isclass(model_identifier):
            try:
                return self.pros_models_by_model_class[model_identifier]
            except KeyError:
                raise ModelManagerException(f"Model {model_identifier} not found.")

        # Get by qualified name
        elif isinstance(model_identifier, str) and "." in model_identifier:
            try:
                return self.pros_models_by_app_name_model_name[
                    to_pascal(model_identifier).lower()
                ]
            except KeyError:
                raise ModelManagerException(f"Model <{model_identifier}> not found.")

        # Get by unqualified name
        elif isinstance(model_identifier, str) and "." not in model_identifier:
            try:
                return self.pros_models_by_model_name[
                    to_pascal(model_identifier).lower()
                ]
            except KeyError:
                raise ModelManagerException(f"Model <{model_identifier}> not found.")

    # Make subscriptable using all options
    __getitem__ = get_model
    __call__ = get_model

    @property
    def models(cls) -> list[AppModel]:
        """Get list of all AppModels in Model Manager"""
        return list(cls.pros_models_by_app_name_model_name.values())


def build_related_reification_dict(
    rel: type[RelationshipDefinition],
) -> ReificationRelationshipType:
    return ReificationRelationshipType(
        target_model_name=rel._raw_class,
        relation_model=rel.definition["model"],
        relation_label=rel.definition["relation_type"],
        relation_manager=rel.manager,
    )


def build_related_reifications(
    model: type[AbstractNode],
) -> dict[str, ReificationRelationshipType]:
    related_reifications: dict[str, ReificationRelationshipType] = {
        n: build_related_reification_dict(p)
        for n, p in model.__all_relationships__
        if p.definition["direction"] == 1
        and issubclass(p.definition["model"], AbstractReificationRelation)
    }
    return related_reifications


def build_subclasses_hierarchy(
    model: type[AbstractNode],
) -> list[SubclassHierarchyItem]:
    return AppModelSet(
        SubclassHierarchyItem(
            model_name=m.__name__.lower(),
            model=m,
            app_name=".".join(m.__module__.split(".")[:-1]),
            subclasses=build_subclasses_hierarchy(m),
        )
        for m in model.__subclasses__()
    )


def build_subclasses_set(model: type[AbstractNode]) -> list[AppModelItem]:
    subclasses = AppModelSet()

    if not model.__subclasses__():
        return subclasses

    for subclass in model.__subclasses__():
        subclasses.add(
            AppModelItem(
                model_name=subclass.__name__,
                model=subclass,
                app_name=".".join(subclass.__module__.split(".")[:-1]),
            )
        )
        subclasses |= build_subclasses_set(subclass)
    return subclasses


def build_parent_classes_set(
    model: type[AbstractNode],
) -> AppModelSet[AppModelItem]:
    return AppModelSet(
        [
            AppModelItem(
                model_name=m.__name__,
                model=m,
                app_name=".".join(m.__module__.split(".")[:-1]),
            )
            for m in inspect.getmro(model)
            if issubclass(m, AbstractNode) and m is not AbstractNode and m is not model
        ]
    )


def build_relation_dict(rel: type[RelationshipDefinition]):
    inline_createable = rel.definition["model"].__dict__.get(
        "to_inline_createable", False
    )

    relation_properties: dict[str, type[Property]] = {
        property_name: property
        for property_name, property in rel.definition["model"].__dict__.items()
        if isinstance(property, Property)
        and property_name not in {"reverse_name", "to_inline_createable"}
    }

    return RelationshipType(
        target_model_name=rel._raw_class,
        relation_model=rel.definition["model"],
        relation_label=rel.definition["relation_type"],
        relation_manager=rel.manager,
        inline_createable=bool(inline_createable),
        has_relation_data=rel.definition["model"].__name__ != "Relation",
        relation_properties=relation_properties,
    )


def build_relationships(model: type[AbstractNode]) -> dict[str, RelationshipType]:
    relations: dict[str, RelationshipType] = {
        n: build_relation_dict(p)
        for n, p in model.__all_relationships__
        if p.definition["direction"] == 1
        and not issubclass(
            p.definition["model"], (AbstractReificationRelation, ChildNodeRelation)
        )
    }
    return relations


@dataclass
class ReverseRelationshipType:
    relationship_from_model_name: str
    relationship_from_model: BaseNode
    reverse_relationship_label: str
    forward_relationship_label: str
    relation_manager: type[RelationshipManager]
    has_relation_data: bool = False
    relation_properties: list[str] = list


def build_reverse_relationships(model) -> dict[str, ReverseRelationshipType]:
    """Reverse relations are defined in REVERSE RELATIONS but we need
    to also get the parent reverse relations"""

    parent_reverse_relations = {}
    for parent_model in inspect.getmro(model):
        if parent_model is AbstractNode:
            break
        parent_reverse_relations = {
            **parent_reverse_relations,
            **REVERSE_RELATIONS[parent_model.__name__],
        }

    reverse_relations = {
        **REVERSE_RELATIONS[model.__name__],
        **parent_reverse_relations,
    }

    packed_reverse_relations = {}
    for rel_name, relation in reverse_relations.items():
        relation_properties = [
            property_name
            for property_name, property in relation["relation"]
            .definition["model"]
            .__dict__.items()
            if isinstance(property, Property)
            and property_name not in {"reverse_name", "to_inline_createable"}
        ]

        rel = ReverseRelationshipType(
            relationship_from_model_name=relation["relation_to"],
            relationship_from_model=relation["relation_to_class"],
            reverse_relationship_label=rel_name,
            forward_relationship_label=relation["relationship_forward_name"],
            relation_manager=relation["relationship_manager"],
            has_relation_data=relation["relation"].definition["model"].__name__
            != "Relation",
            relation_properties=relation_properties,
        )

        packed_reverse_relations[rel_name] = rel
    return packed_reverse_relations


def build_properties(model: type[AbstractNode]) -> DottedDict[str, Property]:
    return DottedDict(
        {
            n: p
            for n, p in model.__all_properties__
            if not isinstance(p, UniqueIdProperty)
            # Internal fields should end with _, which are not settable properties
            if not n.endswith("_")
        }
    )


def build_child_node_dict(rel: type[RelationshipDefinition]):
    return ChildNodeRelationType(
        child_model_name=rel._raw_class,
        relation_label=rel.definition["relation_type"],
        relation_manager=rel.manager,
    )


def build_child_nodes(model: type[AbstractNode]) -> dict[str, ChildNodeRelationType]:
    child_nodes: dict[str, ChildNodeRelationType] = {
        n: build_child_node_dict(p)
        for n, p in model.__all_relationships__
        if p.definition["direction"] == 1
        and issubclass(p.definition["model"], ChildNodeRelation)
    }
    return child_nodes


ModelManager = ModelManagerClass()
