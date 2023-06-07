# PROS CORE

## TODO:

A running list of stuff as it occurs to me

- Reverse relation labels need to be unique for a Node class!


## Notes:

## `ModelManager`, `app_model`, `model`, `pydantic_return_model`, `pydantic_create_model`, `pydantic_edit_model`

Pros models are defined using (customised) `neomodel`-based classes, properties and relation types. `models.py` for a Pros application is the single source of truth.

On starting the application, Pros introspects these models to produce an `app_model` container class, itself held within `ModelManager` (a singleton instance of `ModelManagerClass`), which allows easy lookup of any class. The purpose of `ModelManager` is to enable rapid loooking up of classes without having to introspect `models.py` all the time.

It also stores:
- the app name (`app_model.app_name`)
- the model name (`app_model.model_name`)
- the meta class of a neomodel class as a dict (`app_model.meta`)
- a dict of the properties of a neomodel class (`app_model.properties`)
- a dict of outgoing relations (`app_model.relations`)
- a dict of child nodes (`app_model.child_nodes`)
- a nested structure of a class's subclass hierarchy (`app_model.subclass_hierarchy`)
- a set of a class's subclasses (`app_model.subclasses`)
- a set of a class's parent classes (`app_model.parent_classes`)
- a dict of reverse relations: relations pointing _to_ a class (`app_model.reverse_relationships`)

Reference to the neomodel class from an `app_model` instance is stored as `app_model.model_class`.

It will also hold the pydantic classes for reading, creating and editing ...

### Abstract nodes

There are two types of "abstract" nodes:

1. `__abstract_node__` is from Neomodel; these are not created in at all (similar to Django abstract models)
2. `__abstract__` is a ProsCore setting: is allows a node anywhere in a hierarchy to be designated as "abstract". These are not directly createable, only via a subclass. However, they provide:
    - List view in API
    - Allow relations to such a node, which will allow the creation of one of its subtypes
    - In this respect, similar to Traits (see below), but are inherited and viewable as list

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


