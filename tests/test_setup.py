import pytest
from fastapi.testclient import TestClient
from neomodel import (
    FloatProperty,
    IntegerProperty,
    OneOrMore,
    RelationshipDefinition,
    StringProperty,
    ZeroOrMore,
)
from pros_core.models import AbstractNode, AbstractReification, RelationshipBase
from pros_core.setup_app import setup_app
from pros_core.setup_utils import import_models
from pros_core.setup_utils.model_manager import (
    AppModel,
    ModelManager,
    ModelManagerClass,
    ModelManagerException,
    build_properties,
)
from testing_app.app.core.config import settings
from tests.testing_app.app.main import app

setup_app(app, settings)
"""
def test_api():
    client = TestClient(app)

    response = client.get("/")
    assert response.json() == "pros_core app created!"
"""


def test_import_models():
    from test_app.models import Person

    assert ("test_app", "Person", Person) in import_models(settings)


def test_ModelManager_adding_app_models():
    """Initialise a new ModelManager and check we can add AppModels to it"""

    MM = ModelManagerClass()

    class Thing:
        pass

    app_model = AppModel(
        "test_app",
        Thing,
        "Thing",
        properties={},
        relationships={},
        child_nodes={},
        related_reifications={},
        subclass_hierarchy=[],
        subclasses={},
        parent_classes={},
        reverse_relationships={},
        meta={},
        _mm=MM,
    )
    MM.add_model(app_model)

    assert "testapp.thing" in MM.pros_models_by_app_name_model_name
    assert Thing in MM.pros_models_by_model_class


def test_ModelManager_lookup_fuctions():
    """Create a model manager, and test lookups of an added AppModel"""
    MM = ModelManagerClass()

    class ManyHeadedThing:
        pass

    app_model = AppModel(
        "test_app",
        ManyHeadedThing,
        "ManyHeadedThing",
        properties={},
        relationships={},
        child_nodes={},
        related_reifications={},
        subclass_hierarchy=[],
        subclasses={},
        parent_classes={},
        reverse_relationships={},
        meta={},
        _mm=MM,
    )
    MM.add_model(app_model)

    assert MM.get_model(ManyHeadedThing) == app_model
    assert MM.get_model("TestApp.ManyHeadedThing")
    assert MM.get_model("test_app.manyheadedthing")

    assert MM.models == [app_model]

    # Not there
    with pytest.raises(ModelManagerException):
        MM.get_model("notheretotalbull")

    with pytest.raises(ModelManagerException):
        MM.get_model("LegitFormat.NoModel")

    # Check that the embedded model manager reference works for lookups
    assert app_model._mm.get_model("TestApp.ManyHeadedThing") == app_model


def test_direct_call_and_get_item_on_model_manager():
    from test_app.models import Person

    assert ModelManager("Person")
    assert ModelManager["Person"]
    assert ModelManager[Person]
    assert ModelManager(Person)


def test_build_pros_models():
    assert ModelManager.get_model("TestApp.Entity")
    assert ModelManager.get_model("TestApp.Animal")
    assert ModelManager.get_model("TestApp.Person")


def test_build_properties():
    """Call build_properties on a child object, check it creates correct dict of properties"""

    class TestThing(AbstractNode):
        string_field = StringProperty()
        integer_field = IntegerProperty()

    class TestChildThing(TestThing):
        float_field = FloatProperty()

    assert build_properties(TestChildThing) == {
        "real_type": AbstractNode.real_type,
        "label": AbstractNode.label,
        "created_by": AbstractNode.created_by,
        "created_when": AbstractNode.created_when,
        "modified_by": AbstractNode.modified_by,
        "modified_when": AbstractNode.modified_when,
        "string_field": TestThing.string_field,
        "integer_field": TestThing.integer_field,
        "float_field": TestChildThing.float_field,
        "is_deleted": AbstractNode.is_deleted,
        "last_dependent_change": AbstractNode.last_dependent_change,
    }


def test_relationship_to():
    """Directly test RelationshipTo function, i.e. not as something
    called from within an AbstractNode model"""
    from pros_core.models import REVERSE_RELATIONS, RelationshipTo

    rel = RelationshipTo("Other", "has_other")
    assert isinstance(rel, RelationshipDefinition)
    assert rel._raw_class == "Other"
    assert rel.definition["direction"] == 1
    assert rel.definition["relation_type"] == "Other_has_other"
    assert rel.manager == ZeroOrMore

    # Reverse this write to REVERSE_RELATIONS as it's only testing
    # the function directly -- all else should use the actual setup_app
    # constructors
    del REVERSE_RELATIONS["Other"]


def test_relationship_to_with_options():
    """Directly test RelationshipTo function as above,
    this time not using default relation property class or cardinality class"""
    from pros_core.models import REVERSE_RELATIONS, RelationshipTo

    class CustomRelationType(RelationshipBase):
        pass

    rel = RelationshipTo("Other", "has_other", OneOrMore, CustomRelationType)

    assert isinstance(rel, RelationshipDefinition)
    assert rel._raw_class == "Other"
    assert rel.definition["direction"] == 1
    assert rel.definition["relation_type"] == "Other_has_other"
    assert rel.definition["model"].__name__ == "CustomRelationType"
    assert rel.manager == OneOrMore

    # Reverse this write to REVERSE_RELATIONS as it's only testing
    # the function directly -- all else should use the actual setup_app
    # constructors
    del REVERSE_RELATIONS["Other"]


def test_model_manager_automatically_gets_models():
    from pros_core.setup_utils import ModelManager

    assert ModelManager.get_model("TestApp.Book")
    assert ModelManager.get_model("TestApp.Entity")
    assert ModelManager.get_model("TestApp.Animal")
    assert ModelManager.get_model("TestApp.Person")

    from test_app.models import Animal, Book, Entity, Person

    assert ModelManager.get_model(Book)
    assert ModelManager.get_model(Entity)
    assert ModelManager.get_model(Animal)
    assert ModelManager.get_model(Person)


def test_properties_added_to_app_model():
    from pros_core import ModelManager
    from pros_core.setup_utils.model_manager import build_properties

    class BlankNode(AbstractNode):
        pass

    npn = ModelManager.get_model("TestApp.NoPropertiesNode")
    assert npn.properties

    # The NoPropertiesNode.properties should have the same
    # default properties (created_when, etc.) as another blank node
    assert npn.properties == build_properties(BlankNode)

    # Person, which has a "name" property declared, should
    # also appear in .properties
    person = ModelManager.get_model("TestApp.Person")
    assert "name" in person.properties


def test_relationships_added_to_app_model():
    from pros_core import ModelManager
    from test_app.models import Book

    person = ModelManager.get_model("TestApp.Person")
    assert person.relationships

    assert "has_books" in person.relationships
    assert person.relationships["has_books"].relation_label == "HAS_BOOKS"
    assert person.relationships["has_books"].target_model_name == "Book"
    assert person.relationships["has_books"].target_model is Book
    assert person.relationships["has_books"].target_app_model is ModelManager.get_model(
        "Book"
    )
    assert person.relationships["has_books"].inline_createable is False


def test_app_model_reinjected_into_model():
    from test_app.models import Book, Person

    assert Book._app_model is ModelManager.get_model(Book)
    assert Person._app_model is ModelManager.get_model(Person)


def test_parent_has_child_node():
    from pros_core import ModelManager
    from test_app.models import DateBase, Person

    assert (
        ModelManager.get_model(Person).child_nodes["date_of_birth"].child_model
        == DateBase
    )


def test_createable_inline_relationships_added_to_app_model():
    from pros_core import ModelManager
    from test_app.models import Animal, Person, Pet

    person = ModelManager.get_model("TestApp.Person")
    assert person.relationships

    assert "has_books" in person.relationships
    assert person.relationships["owns_pets"].relation_label == "OWNS_PETS"
    assert person.relationships["owns_pets"].target_model_name == "Pet"
    assert person.relationships["owns_pets"].target_model is Pet
    assert person.relationships["owns_pets"].target_app_model is ModelManager.get_model(
        "Pet"
    )
    assert person.relationships["owns_pets"].inline_createable is True


def test_abstract_reification_added_to_app_model():
    from pros_core import ModelManager
    from test_app.models import Factoid, PersonIdentification

    factoid = ModelManager.get_model("Factoid")
    assert (
        factoid.related_reifications["concerns_person"].target_model
        is PersonIdentification
    )
    assert factoid.related_reifications[
        "concerns_person"
    ].target_app_model is ModelManager.get_model("PersonIdentification")
    assert (
        factoid.related_reifications[
            "concerns_person"
        ].relation_model.reverse_name.default
        == "IS_CONCERNED_IN"
    )


def test_build_subclasses_hierarchy():
    from pros_core.setup_utils.build_app_model_definitions import (
        AppModelSet,
        SubclassHierarchyItem,
        build_subclasses_hierarchy,
    )
    from test_app.models import Animal, Entity, Organisation, Person

    assert build_subclasses_hierarchy(Entity) == AppModelSet(
        [
            SubclassHierarchyItem(
                model_name="animal",
                app_name="pros_testing",
                model=Animal,
                subclasses=[
                    SubclassHierarchyItem(
                        app_name="pros_testing",
                        model_name="person",
                        model=Person,
                        subclasses=[],
                    )
                ],
            ),
            SubclassHierarchyItem(
                model_name="organisation",
                app_name="pros_testing",
                model=Organisation,
                subclasses=[],
            ),
        ]
    )


def test_app_model_subclass_hierarchy():
    from pros_core.setup_utils.build_app_model_definitions import (
        AppModelSet,
        ModelManager,
        SubclassHierarchyItem,
    )
    from test_app.models import Animal, Entity, Organisation, Person

    entity_am = ModelManager.get_model("Entity")
    assert entity_am.subclass_hierarchy == AppModelSet(
        [
            SubclassHierarchyItem(
                model_name="animal",
                app_name="pros_testing",
                model=Animal,
                subclasses=[
                    SubclassHierarchyItem(
                        app_name="pros_testing",
                        model_name="person",
                        model=Person,
                        subclasses=[],
                    )
                ],
            ),
            SubclassHierarchyItem(
                model_name="organisation",
                app_name="pros_testing",
                model=Organisation,
                subclasses=[],
            ),
        ]
    )


def test_build_subclass_list():
    from pros_core.setup_utils.build_app_model_definitions import (
        AppModelItem,
        AppModelSet,
        ModelManager,
        build_subclasses_set,
    )
    from test_app.models import Animal, Entity, Organisation, Person, Pet

    assert build_subclasses_set(Entity) == AppModelSet(
        [
            AppModelItem("Animal", Animal, "pros_testing"),
            AppModelItem("Pet", Pet, "pros_testing"),
            AppModelItem("Person", Person, "pros_testing"),
            AppModelItem("Organisation", Organisation, "pros_testing"),
        ]
    )


def test_app_model_subclass_list():
    from pros_core.setup_utils.build_app_model_definitions import (
        AppModelItem,
        AppModelSet,
        ModelManager,
    )
    from test_app.models import Animal, Entity, Organisation, Person, Pet

    assert ModelManager(Entity).subclasses == AppModelSet(
        [
            AppModelItem("Animal", Animal, "pros_testing"),
            AppModelItem("Pet", Pet, "pros_testing"),
            AppModelItem("Person", Person, "pros_testing"),
            AppModelItem("Organisation", Organisation, "pros_testing"),
        ]
    )

    assert Person in ModelManager(Entity).subclasses

    ModelManager(Entity).subclasses["Person"].app_name


def test_build_parent_class_list():
    from pros_core.setup_utils.build_app_model_definitions import (
        AppModelItem,
        AppModelSet,
        build_parent_classes_set,
    )
    from test_app.models import Animal, Entity, Person

    assert build_parent_classes_set(Person) == AppModelSet(
        [
            AppModelItem(model=Animal, model_name="Animal", app_name="pros_testing"),
            AppModelItem(model=Entity, model_name="Entity", app_name="pros_testing"),
        ]
    )


def test_app_model_parent_class_list():
    from pros_core.setup_utils.build_app_model_definitions import (
        AppModelItem,
        AppModelSet,
        ModelManager,
    )
    from test_app.models import Animal, Entity, Person

    assert ModelManager(Person).parent_classes == AppModelSet(
        [
            AppModelItem(model=Animal, model_name="Animal", app_name="pros_testing"),
            AppModelItem(model=Entity, model_name="Entity", app_name="pros_testing"),
        ]
    )


def test_hashed_app_model_set_and_items():
    from pros_core.setup_utils.build_app_model_definitions import (
        AppModelItem,
        AppModelSet,
    )
    from test_app.models import Animal, Entity, Person

    animal_item = AppModelItem("Animal", Animal, "pros_testing")
    person_item = AppModelItem("Person", Person, "pros_testing")
    subclass_set = AppModelSet([animal_item, person_item])

    assert animal_item == "Animal"

    assert "Animal" in subclass_set
    assert Animal in subclass_set

    assert subclass_set["Animal"]

    # Just check we can also iterate
    for i in subclass_set:
        assert i


def test_build_reverse_relations():
    from pros_core.setup_utils.build_app_model_definitions import (
        ReverseRelationshipType,
        build_reverse_relationships,
    )
    from test_app.models import (
        Book,
        Happening,
        Organisation,
        Ownable,
        Person,
        PersonIdentification,
        Pet,
    )

    assert build_reverse_relationships(Person) == {
        "is_owner_of": ReverseRelationshipType(
            relationship_from_model_name="Ownable",
            relationship_from_model=Ownable,
            reverse_relationship_label="is_owner_of",
            forward_relationship_label="OWNER",
            relation_manager=ZeroOrMore,
            has_relation_data=False,
            relation_properties=[],
        ),
        "is_identified_by": ReverseRelationshipType(
            relationship_from_model_name="PersonIdentification",
            relationship_from_model=PersonIdentification,
            reverse_relationship_label="is_identified_by",
            forward_relationship_label="PERSONS_IDENTIFIED",
            relation_manager=ZeroOrMore,
            has_relation_data=False,
            relation_properties=[],
        ),
        "is_involved_in_happening": ReverseRelationshipType(
            relationship_from_model_name="Happening",
            relationship_from_model=Happening,
            reverse_relationship_label="is_involved_in_happening",
            forward_relationship_label="INVOLVES_ENTITY",
            relation_manager=ZeroOrMore,
            has_relation_data=False,
            relation_properties=[],
        ),
        "is_author_of": ReverseRelationshipType(
            relationship_from_model_name="Book",
            relationship_from_model=Book,
            reverse_relationship_label="is_author_of",
            forward_relationship_label="AUTHOR",
            relation_manager=OneOrMore,
            has_relation_data=False,
            relation_properties=[],
        ),
        "is_member_of": ReverseRelationshipType(
            relationship_from_model_name="Organisation",
            relationship_from_model=Organisation,
            reverse_relationship_label="is_member_of",
            forward_relationship_label="HAS_MEMBER",
            relation_manager=ZeroOrMore,
            has_relation_data=False,
            relation_properties=[],
        ),
    }

    assert build_reverse_relationships(Pet) == {
        "owned_by_person": ReverseRelationshipType(
            relationship_from_model_name="Person",
            relationship_from_model=Person,
            reverse_relationship_label="owned_by_person",
            forward_relationship_label="OWNS_PETS",
            relation_manager=ZeroOrMore,
            has_relation_data=True,
            relation_properties=["purchased_when"],
        ),
        "is_involved_in_happening": ReverseRelationshipType(
            relationship_from_model_name="Happening",
            relationship_from_model=Happening,
            reverse_relationship_label="is_involved_in_happening",
            forward_relationship_label="INVOLVES_ENTITY",
            relation_manager=ZeroOrMore,
            has_relation_data=False,
            relation_properties=[],
        ),
    }


def test_trait_inheritance():
    from test_app.models import Book, DefinitelyNonOwnableBook, NonOwnableBook, Person

    # assert dict(Book.__all_properties__) == {}
    assert "uid" in dict(Book.__all_properties__)
    assert "ownership_type" in dict(Book.__all_properties__)
    assert "owner" in dict(Book.__all_relationships__)
    assert "author" in dict(Book.__all_relationships__)

    assert "author" in dict(NonOwnableBook.__all_relationships__)
    assert "uid" in dict(NonOwnableBook.__all_properties__)
    assert "ownership_type" not in dict(NonOwnableBook.__all_properties__)
    assert "owner" not in dict(NonOwnableBook.__all_relationships__)

    assert "author" in dict(DefinitelyNonOwnableBook.__all_relationships__)
    assert "uid" in dict(DefinitelyNonOwnableBook.__all_properties__)
    assert "ownership_type" not in dict(DefinitelyNonOwnableBook.__all_properties__)
    assert "owner" not in dict(DefinitelyNonOwnableBook.__all_relationships__)

    assert Person.inherited_labels() == ["Person", "Animal", "Entity"]
    assert Book.inherited_labels() == ["Book", "Ownable"]
    assert NonOwnableBook.inherited_labels() == ["NonOwnableBook", "Book"]
    assert DefinitelyNonOwnableBook.inherited_labels() == [
        "DefinitelyNonOwnableBook",
        "NonOwnableBook",
        "Book",
    ]


def test_abstract_trait_gets_real_classes():
    from test_app.models import Book, Ownable, Pet

    assert Ownable.__classes_with_trait__ == {Book, Pet}


def test_import_traits():
    from pros_core.setup_utils.import_models import import_traits
    from test_app.models import Ownable
    from testing_app.app.core.config import settings

    assert import_traits(settings) == [("test_app", "Ownable", Ownable)]


def test_model_manager_has_pydantic_return_class():
    from pros_core import ModelManager

    assert (
        repr(ModelManager("person").pydantic_return_model)
        == "<class 'pydantic.main.Person'>"
    )
