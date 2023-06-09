from neomodel import (
    BooleanProperty,
    DateProperty,
    One,
    OneOrMore,
    StringProperty,
    ZeroOrOne,
)
from pros_core.models import (
    AbstractNode,
    AbstractReification,
    AbstractTrait,
    ChildNode,
    RelationshipBase,
    RelationshipTo,
)


class NoPropertiesNode(AbstractNode):
    pass


class Ownable(AbstractTrait):
    owner = RelationshipTo("Person", "is_owner_of")
    ownership_type = StringProperty()


class Happening(AbstractNode):
    # A relationship to entity, to check the reverse relation also flows down
    # through class hierarchy
    involves_entity = RelationshipTo("Entity", "is_involved_in_happening")


class Entity(AbstractNode):
    pass


class Animal(Entity):
    class Meta:
        something_inheritable = True


class Pet(Animal, Ownable):
    name = StringProperty()


class Calendar(AbstractNode):
    type = StringProperty(default="Julian", choices={"J": "Julian", "G": "Gregorian"})


class DateBase(ChildNode):
    __abstract__ = True

    class Meta:
        abstract = True


class DateImprecise(DateBase):
    date = StringProperty()
    calendar_format = RelationshipTo("Calendar", "is_in_calendar_format")


class DatePrecise(DateBase):
    date = StringProperty()
    calendar_format = RelationshipTo("Calendar", "is_in_calendar_format")


class PetOwnershipRelation(RelationshipBase):
    purchased_when = StringProperty()


class Organisation(Entity):
    has_member = RelationshipTo("Person", "is_member_of")


class Person(Animal):
    name = StringProperty()
    is_male = BooleanProperty(default=True)
    has_books = RelationshipTo("Book", "book_belongs_to_person")
    date_of_birth = DateBase.as_child_node(cardinality=OneOrMore)
    owns_pets = Pet.as_inline_createable(
        "owned_by_person", relationship_model=PetOwnershipRelation
    )
    owns_things = RelationshipTo(
        "Ownable", "thing_belongs_to_person", cardinality=ZeroOrOne
    )
    has_root_vegetable = RelationshipTo(
        "RootVegetable", "root_vegetable_belongs_to_person", cardinality=One
    )

    class Meta:
        display_name_plural = "People"


class PersonIdentification(AbstractReification):
    name_in_text = StringProperty()
    persons_identified = RelationshipTo("Person", "is_identified_by")


class Factoid(AbstractNode):
    concerns_person = PersonIdentification.as_abstract_reification("is_concerned_in")


class Book(AbstractNode, Ownable):
    label = StringProperty()
    author = RelationshipTo("Person", "is_author_of", cardinality=OneOrMore)


class NonOwnableBook(Book):
    pass


class DefinitelyNonOwnableBook(NonOwnableBook):
    pass


class RootVegetable(AbstractNode):
    __abstract__ = True
    label = StringProperty()


class Potato(RootVegetable):
    pass


class Turnip(RootVegetable):
    pass
