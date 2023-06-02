from __future__ import annotations

import datetime
import inspect
from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional, Self, Type

from camel_converter import to_pascal
from dotted_dict import DottedDict
from neomodel import (
    ArrayProperty,
    BooleanProperty,
    DateProperty,
    DateTimeProperty,
    FloatProperty,
    IntegerProperty,
    JSONProperty,
    Property,
    RelationshipDefinition,
    RelationshipManager,
    StringProperty,
    UniqueIdProperty,
)
from ordered_set import OrderedSet
from pros_core.models import (
    REVERSE_RELATIONS,
    AbstractNode,
    AbstractReification,
    AbstractReificationRelation,
    BaseNode,
    ChildNode,
    ChildNodeRelation,
)
from pydantic import UUID4, BaseModel, create_model


@dataclass
class HashableAppModelItem:
    model_name: str
    model: Type[AbstractNode]
    app_name: str

    def __eq__(self, obj) -> bool:
        return self.model_name == obj

    def __hash__(self) -> int:
        return hash(self.model_name)


@dataclass
class SubclassHierarchyItem:
    app_name: str
    model_name: str
    model: Type[AbstractNode]
    subclasses: HashableAppModelItem[Self]

    def __eq__(self, obj) -> bool:
        return self.model_name == obj

    def __hash__(self) -> int:
        return hash(self.model_name)


class HashedAppModelSet(OrderedSet):
    def __getitem__(self, item) -> AppModel:
        return ModelManager(item)

    def __contains__(self, obj: str | Type[AbstractNode]) -> bool:
        if isinstance(obj, str):
            obj = to_pascal(obj)
            return super().__contains__(obj)
        else:
            return super().__contains__(obj.__name__)


@dataclass
class RelationshipType:
    target_model_name: str
    relation_model: Type[RelationshipDefinition]
    relation_label: str
    relation_manager: Type[RelationshipManager]
    inline_createable: bool = False
    has_relation_data: bool = False
    relation_properties: list[str] = list

    @property
    def target_app_model(self) -> AppModel:
        return ModelManager.get_model(self.target_model_name)

    @property
    def target_model(self) -> Type[AbstractNode]:
        return ModelManager.get_model(self.target_model_name).model_class


@dataclass
class ChildNodeRelationType:
    child_model_name: str
    relation_label: str
    relation_manager: Type[RelationshipManager]

    @property
    def child_app_model(self):
        return ModelManager.get_model(self.child_model_name)

    @property
    def child_model(self):
        return ModelManager.get_model(self.child_model_name).model_class


@dataclass
class ReificationRelationshipType:
    target_model_name: str
    relation_model: Type[RelationshipDefinition]
    relation_label: str
    relation_manager: Type[RelationshipManager]

    @property
    def target_app_model(self) -> AppModel:
        return ModelManager.get_model(self.target_model_name)

    @property
    def target_model(self) -> Type[AbstractNode]:
        return ModelManager.get_model(self.target_model_name).model_class


@dataclass
class AppModel:
    app_name: str
    model_class: BaseNode
    model_name: str
    _mm: ModelManagerClass
    # meta: dict
    properties: dict
    relationships: dict[str, RelationshipType]
    child_nodes: dict[str, ChildNodeRelationType]
    related_reifications: dict[str, ReificationRelationshipType]
    subclass_hierarchy: HashableAppModelItem[SubclassHierarchyItem]
    subclasses: HashedAppModelSet[HashableAppModelItem]
    parent_classes: HashedAppModelSet[HashableAppModelItem]
    reverse_relationships: dict[str, dict]


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
        elif "." in model_identifier:
            try:
                return self.pros_models_by_app_name_model_name[
                    to_pascal(model_identifier).lower()
                ]
            except KeyError:
                raise ModelManagerException(f"Model <{model_identifier}> not found.")

        # Get by unqualified name
        elif "." not in model_identifier:
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
    rel: Type[RelationshipDefinition],
) -> ReificationRelationshipType:
    return ReificationRelationshipType(
        target_model_name=rel._raw_class,
        relation_model=rel.definition["model"],
        relation_label=rel.definition["relation_type"],
        relation_manager=rel.manager,
    )


def build_related_reifications(
    model: Type[AbstractNode],
) -> dict[str, ReificationRelationshipType]:
    related_reifications: dict[str, ReificationRelationshipType] = {
        n: build_related_reification_dict(p)
        for n, p in model.__all_relationships__
        if p.definition["direction"] == 1
        and issubclass(p.definition["model"], AbstractReificationRelation)
    }
    return related_reifications


def build_subclasses_hierarchy(
    model: Type[AbstractNode],
) -> list[SubclassHierarchyItem]:
    return HashedAppModelSet(
        SubclassHierarchyItem(
            model_name=m.__name__.lower(),
            model=m,
            app_name=".".join(m.__module__.split(".")[:-1]),
            subclasses=build_subclasses_hierarchy(m),
        )
        for m in model.__subclasses__()
    )


def build_subclasses_set(model: Type[AbstractNode]) -> list[HashableAppModelItem]:
    subclasses = HashedAppModelSet()

    if not model.__subclasses__():
        return subclasses

    for subclass in model.__subclasses__():
        subclasses.add(
            HashableAppModelItem(
                model_name=subclass.__name__,
                model=subclass,
                app_name=".".join(subclass.__module__.split(".")[:-1]),
            )
        )
        subclasses |= build_subclasses_set(subclass)
    return subclasses


def build_parent_classes_set(
    model: Type[AbstractNode],
) -> HashedAppModelSet[HashableAppModelItem]:
    return HashedAppModelSet(
        [
            HashableAppModelItem(
                model_name=m.__name__,
                model=m,
                app_name=".".join(m.__module__.split(".")[:-1]),
            )
            for m in inspect.getmro(model)
            if issubclass(m, AbstractNode) and m is not AbstractNode and m is not model
        ]
    )


def build_relation_dict(rel: Type[RelationshipDefinition]):
    inline_createable = rel.definition["model"].__dict__.get(
        "to_inline_createable", False
    )

    relation_properties = [
        property_name
        for property_name, property in rel.definition["model"].__dict__.items()
        if isinstance(property, Property)
        and property_name not in {"reverse_name", "to_inline_createable"}
    ]

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
    relations: Dict[str, RelationshipType] = {
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
    target_model_name: str
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
            target_model_name=relation["relation_to"],
            reverse_relationship_label=rel_name,
            forward_relationship_label=relation["relationship_forward_name"],
            relation_manager=relation["relationship_manager"],
            has_relation_data=relation["relation"].definition["model"].__name__
            != "Relation",
            relation_properties=relation_properties,
        )

        packed_reverse_relations[rel_name] = rel
    return packed_reverse_relations


def build_properties(model: Type[AbstractNode]) -> DottedDict[str, Property]:
    return DottedDict(
        {
            n: p
            for n, p in model.__all_properties__
            if not isinstance(p, UniqueIdProperty)
            # Internal fields should end with _, which are not settable properties
            if not n.endswith("_")
        }
    )


def build_child_node_dict(rel: Type[RelationshipDefinition]):
    return ChildNodeRelationType(
        child_model_name=rel._raw_class,
        relation_label=rel.definition["relation_type"],
        relation_manager=rel.manager,
    )


def build_child_nodes(model: Type[AbstractNode]) -> Dict[str, ChildNodeRelationType]:
    child_nodes: Dict[str, ChildNodeRelationType] = {
        n: build_child_node_dict(p)
        for n, p in model.__all_relationships__
        if p.definition["direction"] == 1
        and issubclass(p.definition["model"], ChildNodeRelation)
    }
    return child_nodes


from enum import Enum


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


def build_relation_return_model(neomodel_class: type[BaseNode]):
    Model = create_model(
        f"{neomodel_class.__name__}RelationModel",
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
    neomodel_relations = build_child_nodes(neomodel_class)
    pydantic_properties = {}

    for relationship_name, relationship in neomodel_relations.items():
        # TODO: get subtypes with discriminator...
        related_pydantic_model = build_relation_return_model(relationship.child_model)

        pydantic_properties[relationship_name] = (list[related_pydantic_model], ...)

    return pydantic_properties


def build_pydantic_return_model(neomodel_class: type[BaseNode]) -> type[BaseModel]:
    RealTypeLiteral = Enum(  # type: ignore[misc]
        "RealType",
        ((neomodel_class.__name__.lower(), neomodel_class.__name__.lower()),),
        type=str,
    )
    pydantic_properties = build_pydantic_properties(neomodel_class)
    pydantic_relations = build_pydantic_return_relations(neomodel_class)
    pydantic_child_nodes = build_pydantic_return_child_nodes(neomodel_class)
    Model = create_model(
        f"{neomodel_class.__name__}",
        real_type=(RealTypeLiteral, neomodel_class.__name__.lower()),
        **pydantic_properties,
        **pydantic_relations,
        **pydantic_child_nodes,
    )
    print(Model.schema())
    return Model


ModelManager = ModelManagerClass()


def create_app_model(
    app_name: str, model_class: Type[BaseNode], model_name: str, _mm: ModelManagerClass
) -> AppModel:
    return AppModel(
        app_name=to_pascal(app_name),
        model_class=model_class,
        model_name=model_name,
        properties=build_properties(model=model_class),
        relationships=build_relationships(model=model_class),
        child_nodes=build_child_nodes(model=model_class),
        related_reifications=build_related_reifications(model=model_class),
        subclass_hierarchy=build_subclasses_hierarchy(model=model_class),
        subclasses=build_subclasses_set(model=model_class),
        parent_classes=build_parent_classes_set(model=model_class),
        reverse_relationships=build_reverse_relationships(model=model_class),
        _mm=_mm,
    )


def setup_model_manager(pros_models: list[tuple(str, type[BaseNode])]) -> None:
    for app_name, model_name, model in pros_models:
        # Check if it's a class defined in this model (not imported from somewhere)
        # and that it's a top-level node

        # Create AppModel for each model and add to ModelManager
        app_model = create_app_model(
            app_name=app_name,
            model_class=model,
            model_name=model_name,
            _mm=ModelManager,
        )
        ModelManager.add_model(app_model)

        # And sling the app_model onto the model itself for good measure
        model._app_model: AppModel = app_model
