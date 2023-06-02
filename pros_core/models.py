from __future__ import annotations

import datetime
import inspect
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


class BaseStructuredNode(StructuredNode):
    __abstract_node__ = True

    @staticmethod
    def is_abstract_trait(cls) -> bool:
        return getattr(cls, "__is_trait__", False)

    """ TODO: Seemingly not necessary; remove later
    @classmethod
    def has_trait_as_direct_base(cls):
        trait_is_direct_base = False

        for base in cls.__bases__:
            base_is_trait = False
            for parent in inspect.getmro(base):
                if parent.__name__ == "AbstractNode":
                    break
                elif parent.__name__ == "AbstractTrait":
                    base_is_trait = True
                else:
                    continue
            trait_is_direct_base = base_is_trait
        return trait_is_direct_base
    """

    @classmethod
    def traits_as_direct_base(cls) -> set[AbstractTrait]:
        traits_as_direct_bases = []
        if getattr(cls, "__is_trait__", False):
            traits_as_direct_bases.append(cls)
        for base in cls.__bases__:
            for parent in inspect.getmro(base):
                if parent.__name__ == "AbstractNode":
                    break
                elif parent.__name__ == "AbstractTrait":
                    traits_as_direct_bases.append(base)
                else:
                    continue
        return set(traits_as_direct_bases)

    @classmethod
    def inherited_labels(cls) -> list[str]:
        """
        Return list of labels from nodes class hierarchy.

        :return: list
        """
        # Overrides the neomodel StructuredNode method to exclude labels from
        # inherited traits

        inherited = []
        for scls in cls.__mro__:
            if hasattr(scls, "__label__"):
                if cls.is_abstract_trait(scls) and scls not in cls.__bases__:
                    continue

                inherited.append(scls.__label__)

        return inherited

    @classmethod
    def defined_properties(cls, aliases=True, properties=True, rels=True):
        # Overrides the neomodel StructureNode method to get only properties/relationships
        # that come from current class, parent BaseNodes and direct traits

        from neomodel import AliasProperty, Property
        from neomodel.relationship_manager import RelationshipDefinition

        props = {}
        for baseclass in reversed(cls.__mro__):
            if (
                cls.is_abstract_trait(baseclass)
                and baseclass not in cls.traits_as_direct_base()
            ):
                continue
            props.update(
                dict(
                    (name, property)
                    for name, property in vars(baseclass).items()
                    if (aliases and isinstance(property, AliasProperty))
                    or (
                        properties
                        and isinstance(property, Property)
                        and not isinstance(property, AliasProperty)
                    )
                    or (rels and isinstance(property, RelationshipDefinition))
                )
            )

        return props

    def __init_subclass__(cls) -> None:
        # Add to REVERSE_RELATIONS dict the info from the side of the possessing class

        super().__init_subclass__()

        # Introspect the class for relations, and add the relation information
        # to the REVERSE_RELATIONS dict
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


class BaseNode(BaseStructuredNode):
    """Base for all Neomodel nodes"""

    __abstract_node__ = True

    # Fields appearing in BaseNode.Meta that should not be inherited by subclasses
    NON_INHERITABLE_META_FIELDS = ["display_name", "display_name_plural", "abstract"]

    class Meta:
        pass

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.__is_trait__ = False

        # Build the class Meta class and the cls._meta dict
        base_attrs = {}

        # Get all the attributes of the base classes
        for base in list(cls.__bases__):
            base_attrs = {**getattr(base, "Meta").__dict__}

        # Remove attributes that should not be inherited
        for remove_field in cls.NON_INHERITABLE_META_FIELDS:
            base_attrs.pop(remove_field, None)

        # Create meta attributes using base attributes and attributes of the current class
        meta_attrs = {**base_attrs, **cls.__dict__.get("Meta", __class__.Meta).__dict__}

        # Create a new Meta class and assign it to the class
        cls.Meta = type(
            "Meta",
            (__class__.Meta,),
            meta_attrs,
        )

        # For convenience, make this into a dict on the class
        cls._meta = {
            k: v
            for k, v in cls.Meta.__dict__.items()
            if not k.startswith("__") and not k.endswith("__")
        }

        for trait in cls.traits_as_direct_base():
            trait.__classes_with_trait__.add(cls)


class AbstractTrait(BaseStructuredNode):
    __abstract_node__ = True
    __is_trait__ = True

    class Meta:
        pass

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.__classes_with_trait__ = set()


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
    def as_child_node(cls, cardinality=One) -> RelationshipDefinition:
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
