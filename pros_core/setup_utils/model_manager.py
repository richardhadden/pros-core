from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Dict, Self, Type

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
    AbstractReification,
    AbstractReificationRelation,
    BaseNode,
    ChildNode,
    ChildNodeRelation,
)


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


def build_reverse_relationships(model):
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

    return {**REVERSE_RELATIONS[model.__name__], **parent_reverse_relations}


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
