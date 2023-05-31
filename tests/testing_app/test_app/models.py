from neomodel import DateProperty, One, StringProperty
from pros_core.models import (
    AbstractNode,
    AbstractReification,
    ChildNode,
    RelationshipBase,
    RelationshipTo,
)


class NoPropertiesNode(AbstractNode):
    pass


class Book(AbstractNode):
    label = StringProperty()


class Happening(AbstractNode):
    # A relationship to entity, to check the reverse relation also flows down
    # through class hierarchy
    involves_entity = RelationshipTo("Entity", "is_involved_in_happening")


class Entity(AbstractNode):
    pass


class Animal(Entity):
    pass


class Pet(Animal):
    name = StringProperty()


class Calendar(AbstractNode):
    type = StringProperty(default="Julian")


class Date(ChildNode):
    date = StringProperty()
    calendar_format = RelationshipTo("Calendar", "is_in_calendar_format")


class PetOwnershipRelation(RelationshipBase):
    purchased_when = StringProperty()


class Person(Animal):
    name = StringProperty()
    has_books = RelationshipTo("Book", "belongs_to_person")
    date_of_birth = Date.as_child_node()
    owns_pets = Pet.as_inline_createable(
        "owned_by_person", relationship_model=PetOwnershipRelation
    )


class PersonIdentification(AbstractReification):
    name_in_text = StringProperty()
    persons_identified = RelationshipTo("Person", "is_identified_by")


class Factoid(AbstractNode):
    concerns_person = PersonIdentification.as_abstract_reification("is_concerned_in")
