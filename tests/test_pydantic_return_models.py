from typing import Union, get_args, get_origin, get_type_hints

import pydantic
import pytest
from pros_core.setup_app import setup_app
from pydantic.types import ConstrainedList
from testing_app.app.core.config import settings
from testing_app.app.main import app


def test_build_pydantic_return_child_nodes():
    from pros_core.setup_utils.build_pydantic_return_models import (
        build_pydantic_return_child_nodes,
    )
    from test_app.models import Person

    types: ConstrainedList = build_pydantic_return_child_nodes(Person)
    assert types["date_of_birth"]

    assert types["date_of_birth"][0].min_items == 1


def test_build_pydantic_model_for_person():
    from pros_core.setup_utils.build_pydantic_return_models import (
        build_pydantic_return_model,
        build_relation_return_model,
    )
    from test_app.models import Calendar, Person

    PydanticPerson = build_pydantic_return_model(Person)

    s = PydanticPerson.schema()
    # assert s == {}
    assert s["title"] == "Person"
    assert s["type"] == "object"
    assert s["properties"]["real_type"]
    real_type = s["properties"]["real_type"]
    assert real_type["title"] == "Real Type"
    assert real_type["default"] == "person"
    assert real_type["enum"] == ["person"]
    assert real_type["type"] == "string"

    assert s["properties"]["label"] == {"title": "Label", "type": "string"}
    assert s["properties"]["created_by"] == {"title": "Created By", "type": "string"}
    assert s["properties"]["created_when"] == {
        "title": "Created When",
        "type": "string",
        "format": "date-time",
    }
    assert s["properties"]["modified_by"] == {"title": "Modified By", "type": "string"}
    assert s["properties"]["modified_when"] == {
        "title": "Modified When",
        "type": "string",
        "format": "date-time",
    }
    assert s["properties"]["is_deleted"] == {
        "title": "Is Deleted",
        "default": False,
        "type": "boolean",
    }

    assert s["properties"]["last_dependent_change"] == {
        "title": "Last Dependent Change",
        "type": "string",
        "format": "date-time",
    }
    assert s["properties"]["name"] == {"title": "Name", "type": "string"}
    assert s["properties"]["is_male"] == {
        "title": "Is Male",
        "default": True,
        "type": "boolean",
    }

    has_books = s["properties"]["has_books"]
    assert has_books
    assert has_books["title"] == "Has Books"
    assert has_books["uniqueItems"] == True
    assert has_books["type"] == "array"
    has_books_items = has_books["items"]
    assert has_books_items
    assert has_books_items["anyOf"]
    assert len(has_books_items["anyOf"]) == 3
    assert {"$ref": "#/definitions/Person_HasBooks_Book_Related"} in has_books_items[
        "anyOf"
    ]
    assert {
        "$ref": "#/definitions/Person_HasBooks_NonOwnableBook_Related"
    } in has_books_items["anyOf"]
    assert {
        "$ref": "#/definitions/Person_HasBooks_DefinitelyNonOwnableBook_Related"
    } in has_books_items["anyOf"]

    assert s["properties"]["owns_pets"] == {
        "title": "Owns Pets",
        "uniqueItems": True,
        "type": "array",
        "items": {"$ref": "#/definitions/Person_OwnsPets_Pet_Related"},
    }

    owns_things = s["properties"]["owns_things"]
    assert owns_things

    assert owns_things["title"] == "Owns Things"
    assert owns_things["maxItems"] == 1
    assert owns_things["uniqueItems"] == True
    assert owns_things["type"] == "array"
    owns_things_items = owns_things["items"]
    assert owns_things_items
    assert len(owns_things_items["anyOf"]) == 2
    assert {"$ref": "#/definitions/Person_OwnsThings_Pet_Related"} in owns_things_items[
        "anyOf"
    ]
    assert {
        "$ref": "#/definitions/Person_OwnsThings_Book_Related"
    } in owns_things_items["anyOf"]

    has_root_vegetable = s["properties"]["has_root_vegetable"]
    assert has_root_vegetable
    assert has_root_vegetable["title"] == "Has Root Vegetable"
    assert has_root_vegetable["minItems"] == 1
    assert has_root_vegetable["maxItems"] == 1
    assert has_root_vegetable["uniqueItems"] == True
    assert has_root_vegetable["type"] == "array"
    has_root_vegetable_items = has_root_vegetable["items"]
    assert has_root_vegetable_items
    assert len(has_root_vegetable_items["anyOf"]) == 2
    assert {
        "$ref": "#/definitions/Person_HasRootVegetable_Potato_Related"
    } in has_root_vegetable_items["anyOf"]
    assert {
        "$ref": "#/definitions/Person_HasRootVegetable_Turnip_Related"
    } in has_root_vegetable_items["anyOf"]

    is_owner_of = s["properties"]["is_owner_of"]
    assert is_owner_of
    assert is_owner_of["title"] == "Is Owner Of"
    assert is_owner_of["type"] == "array"
    is_owner_of_items = is_owner_of["items"]
    assert len(is_owner_of_items["anyOf"]) == 2
    assert {"$ref": "#/definitions/Pet_Owner_Person_Related"} in is_owner_of_items[
        "anyOf"
    ]
    assert {"$ref": "#/definitions/Book_Owner_Person_Related"} in is_owner_of_items[
        "anyOf"
    ]

    assert s["properties"]["is_member_of"] == {
        "title": "Is Member Of",
        "type": "array",
        "items": {"$ref": "#/definitions/Organisation_HasMember_Person_Related"},
    }

    assert s["properties"]["is_identified_by"] == {
        "title": "Is Identified By",
        "type": "array",
        "items": {
            "$ref": "#/definitions/PersonIdentification_PersonsIdentified_Person_Related"
        },
    }

    is_author_of = s["properties"]["is_author_of"]
    assert is_author_of
    assert is_author_of["title"] == "Is Author Of"
    assert is_author_of["type"] == "array"
    is_author_of_items = is_author_of["items"]
    assert is_author_of_items
    assert len(is_author_of_items["anyOf"]) == 3
    assert {"$ref": "#/definitions/Book_Author_Person_Related"} in is_author_of_items[
        "anyOf"
    ]

    assert s["properties"]["is_involved_in_happening"] == {
        "title": "Is Involved In Happening",
        "type": "array",
        "items": {"$ref": "#/definitions/Happening_InvolvesEntity_Person_Related"},
    }

    assert s["required"] == [
        "last_dependent_change",
        "has_books",
        "owns_pets",
        "owns_things",
        "has_root_vegetable",
        "date_of_birth",
    ]

    assert s["definitions"] == {
        "Person_HasBooks_Book_Related": {
            "title": "Person_HasBooks_Book_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "book",
                    "enum": ["book"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_HasBooks_NonOwnableBook_Related": {
            "title": "Person_HasBooks_NonOwnableBook_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "nonownablebook",
                    "enum": ["nonownablebook"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_HasBooks_DefinitelyNonOwnableBook_Related": {
            "title": "Person_HasBooks_DefinitelyNonOwnableBook_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "definitelynonownablebook",
                    "enum": ["definitelynonownablebook"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_OwnsPets_Pet_Related_RelationData": {
            "title": "Person_OwnsPets_Pet_Related_RelationData",
            "type": "object",
            "properties": {
                "purchased_when": {"title": "Purchased When", "type": "string"}
            },
        },
        "Person_OwnsPets_Pet_Related": {
            "title": "Person_OwnsPets_Pet_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "pet",
                    "enum": ["pet"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
                "relation_data": {
                    "$ref": "#/definitions/Person_OwnsPets_Pet_Related_RelationData"
                },
            },
            "required": ["label", "uid", "relation_data"],
        },
        "Person_OwnsThings_Book_Related": {
            "title": "Person_OwnsThings_Book_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "book",
                    "enum": ["book"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_OwnsThings_Pet_Related": {
            "title": "Person_OwnsThings_Pet_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "pet",
                    "enum": ["pet"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_HasRootVegetable_Potato_Related": {
            "title": "Person_HasRootVegetable_Potato_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "potato",
                    "enum": ["potato"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_HasRootVegetable_Turnip_Related": {
            "title": "Person_HasRootVegetable_Turnip_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "turnip",
                    "enum": ["turnip"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "DateImprecise_CalendarFormat_Calendar_Related": {
            "title": "DateImprecise_CalendarFormat_Calendar_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "calendar",
                    "enum": ["calendar"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "DateImprecise": {
            "title": "DateImprecise",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "dateimprecise",
                    "enum": ["dateimprecise"],
                    "type": "string",
                },
                "date": {"title": "Date", "type": "string"},
                "calendar_format": {
                    "title": "Calendar Format",
                    "uniqueItems": True,
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/DateImprecise_CalendarFormat_Calendar_Related"
                    },
                },
            },
            "required": ["calendar_format"],
        },
        "DatePrecise_CalendarFormat_Calendar_Related": {
            "title": "DatePrecise_CalendarFormat_Calendar_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "calendar",
                    "enum": ["calendar"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "DatePrecise": {
            "title": "DatePrecise",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "dateprecise",
                    "enum": ["dateprecise"],
                    "type": "string",
                },
                "date": {"title": "Date", "type": "string"},
                "calendar_format": {
                    "title": "Calendar Format",
                    "uniqueItems": True,
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/DatePrecise_CalendarFormat_Calendar_Related"
                    },
                },
            },
            "required": ["calendar_format"],
        },
        "Book_Owner_Person_Related": {
            "title": "Book_Owner_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Pet_Owner_Person_Related": {
            "title": "Pet_Owner_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Organisation_HasMember_Person_Related": {
            "title": "Organisation_HasMember_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "PersonIdentification_PersonsIdentified_Person_Related": {
            "title": "PersonIdentification_PersonsIdentified_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Book_Author_Person_Related": {
            "title": "Book_Author_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "NonOwnableBook_Author_Person_Related": {
            "title": "NonOwnableBook_Author_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "DefinitelyNonOwnableBook_Author_Person_Related": {
            "title": "DefinitelyNonOwnableBook_Author_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Happening_InvolvesEntity_Person_Related": {
            "title": "Happening_InvolvesEntity_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
    }


{
    "title": "Person",
    "type": "object",
    "properties": {
        "real_type": {
            "title": "Real Type",
            "default": "person",
            "enum": ["person"],
            "type": "string",
        },
        "label": {"title": "Label", "type": "string"},
        "created_by": {"title": "Created By", "type": "string"},
        "created_when": {
            "title": "Created When",
            "type": "string",
            "format": "date-time",
        },
        "modified_by": {"title": "Modified By", "type": "string"},
        "modified_when": {
            "title": "Modified When",
            "type": "string",
            "format": "date-time",
        },
        "is_deleted": {"title": "Is Deleted", "default": False, "type": "boolean"},
        "last_dependent_change": {
            "title": "Last Dependent Change",
            "type": "string",
            "format": "date-time",
        },
        "name": {"title": "Name", "type": "string"},
        "is_male": {"title": "Is Male", "default": True, "type": "boolean"},
        "has_books": {
            "title": "Has Books",
            "uniqueItems": True,
            "type": "array",
            "items": {
                "anyOf": [
                    {"$ref": "#/definitions/Person_HasBooks_Book_Related"},
                    {"$ref": "#/definitions/Person_HasBooks_NonOwnableBook_Related"},
                    {
                        "$ref": "#/definitions/Person_HasBooks_DefinitelyNonOwnableBook_Related"
                    },
                ]
            },
        },
        "owns_pets": {
            "title": "Owns Pets",
            "uniqueItems": True,
            "type": "array",
            "items": {"$ref": "#/definitions/Person_OwnsPets_Pet_Related"},
        },
        "owns_things": {
            "title": "Owns Things",
            "maxItems": 1,
            "uniqueItems": True,
            "type": "array",
            "items": {
                "anyOf": [
                    {"$ref": "#/definitions/Person_OwnsThings_Book_Related"},
                    {"$ref": "#/definitions/Person_OwnsThings_Pet_Related"},
                ]
            },
        },
        "has_root_vegetable": {
            "title": "Has Root Vegetable",
            "minItems": 1,
            "maxItems": 1,
            "uniqueItems": True,
            "type": "array",
            "items": {
                "anyOf": [
                    {"$ref": "#/definitions/Person_HasRootVegetable_Potato_Related"},
                    {"$ref": "#/definitions/Person_HasRootVegetable_Turnip_Related"},
                ]
            },
        },
        "date_of_birth": {
            "title": "Date Of Birth",
            "minItems": 1,
            "uniqueItems": True,
            "type": "array",
            "items": {
                "anyOf": [
                    {"$ref": "#/definitions/DateImprecise"},
                    {"$ref": "#/definitions/DatePrecise"},
                ]
            },
        },
        "is_owner_of": {
            "title": "Is Owner Of",
            "type": "array",
            "items": {
                "anyOf": [
                    {"$ref": "#/definitions/Book_Owner_Person_Related"},
                    {"$ref": "#/definitions/Pet_Owner_Person_Related"},
                ]
            },
        },
        "is_member_of": {
            "title": "Is Member Of",
            "type": "array",
            "items": {"$ref": "#/definitions/Organisation_HasMember_Person_Related"},
        },
        "is_identified_by": {
            "title": "Is Identified By",
            "type": "array",
            "items": {
                "$ref": "#/definitions/PersonIdentification_PersonsIdentified_Person_Related"
            },
        },
        "is_author_of": {
            "title": "Is Author Of",
            "type": "array",
            "items": {
                "anyOf": [
                    {"$ref": "#/definitions/Book_Author_Person_Related"},
                    {"$ref": "#/definitions/NonOwnableBook_Author_Person_Related"},
                    {
                        "$ref": "#/definitions/DefinitelyNonOwnableBook_Author_Person_Related"
                    },
                ]
            },
        },
        "is_involved_in_happening": {
            "title": "Is Involved In Happening",
            "type": "array",
            "items": {"$ref": "#/definitions/Happening_InvolvesEntity_Person_Related"},
        },
    },
    "required": [
        "last_dependent_change",
        "has_books",
        "owns_pets",
        "owns_things",
        "has_root_vegetable",
        "date_of_birth",
    ],
    "definitions": {
        "Person_HasBooks_Book_Related": {
            "title": "Person_HasBooks_Book_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "book",
                    "enum": ["book"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_HasBooks_NonOwnableBook_Related": {
            "title": "Person_HasBooks_NonOwnableBook_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "nonownablebook",
                    "enum": ["nonownablebook"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_HasBooks_DefinitelyNonOwnableBook_Related": {
            "title": "Person_HasBooks_DefinitelyNonOwnableBook_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "definitelynonownablebook",
                    "enum": ["definitelynonownablebook"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_OwnsPets_Pet_Related_RelationData": {
            "title": "Person_OwnsPets_Pet_Related_RelationData",
            "type": "object",
            "properties": {
                "purchased_when": {"title": "Purchased When", "type": "string"}
            },
        },
        "Person_OwnsPets_Pet_Related": {
            "title": "Person_OwnsPets_Pet_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "pet",
                    "enum": ["pet"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
                "relation_data": {
                    "$ref": "#/definitions/Person_OwnsPets_Pet_Related_RelationData"
                },
            },
            "required": ["label", "uid", "relation_data"],
        },
        "Person_OwnsThings_Book_Related": {
            "title": "Person_OwnsThings_Book_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "book",
                    "enum": ["book"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_OwnsThings_Pet_Related": {
            "title": "Person_OwnsThings_Pet_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "pet",
                    "enum": ["pet"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_HasRootVegetable_Potato_Related": {
            "title": "Person_HasRootVegetable_Potato_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "potato",
                    "enum": ["potato"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_HasRootVegetable_Turnip_Related": {
            "title": "Person_HasRootVegetable_Turnip_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "turnip",
                    "enum": ["turnip"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "DateImprecise_CalendarFormat_Calendar_Related": {
            "title": "DateImprecise_CalendarFormat_Calendar_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "calendar",
                    "enum": ["calendar"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "DateImprecise": {
            "title": "DateImprecise",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "dateimprecise",
                    "enum": ["dateimprecise"],
                    "type": "string",
                },
                "date": {"title": "Date", "type": "string"},
                "calendar_format": {
                    "title": "Calendar Format",
                    "uniqueItems": True,
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/DateImprecise_CalendarFormat_Calendar_Related"
                    },
                },
            },
            "required": ["calendar_format"],
        },
        "DatePrecise_CalendarFormat_Calendar_Related": {
            "title": "DatePrecise_CalendarFormat_Calendar_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "calendar",
                    "enum": ["calendar"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "DatePrecise": {
            "title": "DatePrecise",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "dateprecise",
                    "enum": ["dateprecise"],
                    "type": "string",
                },
                "date": {"title": "Date", "type": "string"},
                "calendar_format": {
                    "title": "Calendar Format",
                    "uniqueItems": True,
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/DatePrecise_CalendarFormat_Calendar_Related"
                    },
                },
            },
            "required": ["calendar_format"],
        },
        "Book_Owner_Person_Related": {
            "title": "Book_Owner_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Pet_Owner_Person_Related": {
            "title": "Pet_Owner_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Organisation_HasMember_Person_Related": {
            "title": "Organisation_HasMember_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "PersonIdentification_PersonsIdentified_Person_Related": {
            "title": "PersonIdentification_PersonsIdentified_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Book_Author_Person_Related": {
            "title": "Book_Author_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "NonOwnableBook_Author_Person_Related": {
            "title": "NonOwnableBook_Author_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "DefinitelyNonOwnableBook_Author_Person_Related": {
            "title": "DefinitelyNonOwnableBook_Author_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Happening_InvolvesEntity_Person_Related": {
            "title": "Happening_InvolvesEntity_Person_Related",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "person",
                    "enum": ["person"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
    },
}
