from __future__ import annotations

import datetime
from collections import defaultdict
from typing import TYPE_CHECKING, DefaultDict, Optional, Type

from neomodel import (
    BooleanProperty,
    DateTimeProperty,
    One,
    OneOrMore,
    RelationshipDefinition,
    RelationshipManager,
)
from neomodel import RelationshipTo as neomodelRelationshipTo
from neomodel import (
    StringProperty,
    StructuredNode,
    StructuredRel,
    UniqueIdProperty,
    ZeroOrMore,
    ZeroOrOne,
)

if TYPE_CHECKING:
    from setup_app import AppModel

REVERSE_RELATIONS: DefaultDict[str, DefaultDict[str, dict]] = defaultdict(
    lambda: defaultdict(dict)
)


class BaseNode(StructuredNode):
    """Base for all Neomodel nodes"""

    __abstract_node__ = True

    def __init_subclass__(cls) -> None:
        # Add to REVERSE_RELATIONS dict the info from the side of the possessing class
        for k, v in cls.__dict__.items():
            if isinstance(v, RelationshipDefinition):
                try:
                    v.definition["relation_type"] = k.upper()
                    rr = REVERSE_RELATIONS[v._raw_class][
                        v.definition["model"].__dict__["reverse_name"].default.lower()
                    ]
                    rr["relation"] = v
                    rr["relation_to"] = cls.__name__
                    rr["relationship_forward_name"] = v.definition["relation_type"]
                    rr["relationship_manager"] = v.manager

                except:
                    pass


class InlineCreateableRelation(StructuredRel):
    """Does not do anything except designate that a class is being used
    as inline_createable."""

    to_inline_createable = BooleanProperty(default=True)


class ChildNodeRelation(StructuredRel):
    """Does not do anything useful as a class, except provide a hook to
    determine whether a relation is to child_node or not. Can use the 'to_child_node'
    field value (when getting data), or class relation (during setup)
    to determine this."""

    to_child_node = BooleanProperty(default=True)


class ChildNode(BaseNode):
    __abstract_node__ = True

    @classmethod
    def as_child_node(cls, cardinality=One):
        return neomodelRelationshipTo(
            cls.__name__,
            f"NOT SET",
            cardinality=cardinality or ZeroOrOne,
            model=ChildNodeRelation,
        )


class AbstractReificationRelation(StructuredRel):
    """Does not do anything useful as a class, except provide a hook to
    determine whether a relation is to an abstract_reification or not. Can use the 'to_abstract_reification'
    field value (when getting data), or class relation (during setup)
    to determine this."""

    to_abstract_reification = BooleanProperty(default=True)


class AbstractReification(BaseNode):
    __abstract_node__ = True

    @classmethod
    def as_abstract_reification(cls, reverse_name="", cardinality=ZeroOrMore):
        return neomodelRelationshipTo(
            cls.__name__,
            f"{cls.__name__}_{reverse_name}",
            cardinality=cardinality or ZeroOrOne,
            model=type(
                "ReificationRelation",
                (AbstractReificationRelation,),
                {"reverse_name": StringProperty(default=reverse_name.upper())},
            ),
        )


class AbstractNode(BaseNode):
    """Base for standard node types"""

    __abstract_node__ = True
    _app_model: AppModel

    uid = UniqueIdProperty()
    label = StringProperty(index=True)
    real_type = StringProperty(index=True)
    created_by = StringProperty()
    created_when = DateTimeProperty()
    modified_by = StringProperty()
    modified_when = DateTimeProperty()
    is_deleted = BooleanProperty(default=False)
    last_dependent_change = DateTimeProperty(default=lambda: datetime.datetime.utcnow())

    def save(self, *args, **kwargs):
        self.real_type = type(self).__name__
        super().save(*args, **kwargs)

    @classmethod
    def as_inline_createable(
        cls,
        reverse_name: str,
        cardinality: RelationshipManager = ZeroOrMore,
        relationship_model: Type[RelationshipBase] = None,
    ) -> RelationshipDefinition:
        """Allows creation of nodes inline in the parent class. Once added, they can not be edited
        but function like normal relationships."""

        relationship_model_to_use = (
            type(
                relationship_model.__name__,
                (relationship_model,),
                {
                    "reverse_name": StringProperty(default=reverse_name.upper()),
                    "to_inline_createable": BooleanProperty(default=True),
                    **relationship_model.__dict__,
                },
            )
            if relationship_model
            else type(
                "InlineRelation",
                (InlineCreateableRelation,),
                {
                    "reverse_name": StringProperty(default=reverse_name.upper()),
                    "to_inline_createable": BooleanProperty(default=True),
                },
            )
        )

        return neomodelRelationshipTo(
            cls.__name__,
            f"{cls.__name__}_{reverse_name}",
            cardinality=cardinality or ZeroOrMore,
            model=relationship_model_to_use,
        )


class DeletedNode(StructuredNode):
    pass


class RelationshipBase(StructuredRel):
    reverse_name = StringProperty(required=True)


def RelationshipTo(
    target_class_name,
    reverse_name: str,
    cardinality=None,
    relationship_model=None,
    help_text: Optional[str] = None,
) -> RelationshipDefinition:
    m: Type[RelationshipBase] = type(
        relationship_model.__name__ if relationship_model else "Relation",
        (relationship_model if relationship_model else RelationshipBase,),
        {
            "reverse_name": StringProperty(default=reverse_name.upper()),
            **relationship_model.__dict__,
        }
        if relationship_model
        else {"reverse_name": StringProperty(default=reverse_name.upper())},
    )
    m.help_text = help_text

    # Add to the reverse name the class from the side of the target
    REVERSE_RELATIONS[target_class_name][reverse_name.lower()]

    return neomodelRelationshipTo(
        target_class_name,
        f"{target_class_name}_{reverse_name}",
        cardinality=cardinality or ZeroOrMore,
        model=m,
    )
