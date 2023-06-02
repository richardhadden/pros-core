# PROS CORE


## Notes:

### Traits
Traits are like mixins, but allow cutting across hierarchies

Traits apply to the class to which they are applied *only*:

```python

# Allows an object to be "ownable" by supplying it with an ownership_type property
# and a relation to a Person who owns the thing.
class Ownable(AbstractTrait):
    owner = RelationshipTo("Person", "is_owner_of")
    ownership_type = StringProperty()


# A default book is ownable, using the Ownable trait; is has the relationship to `owner`
# and the field `ownership_type`
class Book(AbstractNode, Ownable):
    label = StringProperty()
    author = RelationshipTo("Person", "is_author_of")

# NonOwnableBook is not ownable (even though it inherits from Book)
# It inherits the standard fields from Book and above (`label`, `author`, etc.)
# but not `owner` relation or `ownership_type` field
class NonOwnableBook(Book):
    pass


# Pets are also "ownable"
class Pet(AbstractNode, Ownable):
    name = StringProperty()

```

Traits can also be *related to* by other models. e.g. 

```python
class Confiscation(AbstractNode):
    thing_confiscated = RelationshipTo("Ownable", "was_confiscated_in")
```

will allow `Confiscation` to be connected to anything that is *directly* ownable, i.e. `Book` and `Pet`.

