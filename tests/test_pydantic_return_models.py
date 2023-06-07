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
    assert s["properties"]["realType"]
    real_type = s["properties"]["realType"]
    assert real_type["title"] == "Realtype"
    assert real_type["default"] == "person"
    assert real_type["enum"] == ["person"]
    assert real_type["type"] == "string"

    assert "uid" in s["properties"]
    assert s["properties"]["label"] == {"title": "Label", "type": "string"}
    assert s["properties"]["createdBy"] == {"title": "Createdby", "type": "string"}
    assert s["properties"]["createdWhen"] == {
        "title": "Createdwhen",
        "type": "string",
        "format": "date-time",
    }
    assert s["properties"]["modifiedBy"] == {"title": "Modifiedby", "type": "string"}
    assert s["properties"]["modifiedWhen"] == {
        "title": "Modifiedwhen",
        "type": "string",
        "format": "date-time",
    }
    assert s["properties"]["isDeleted"] == {
        "title": "Isdeleted",
        "default": False,
        "type": "boolean",
    }

    assert s["properties"]["lastDependentChange"] == {
        "title": "Lastdependentchange",
        "type": "string",
        "format": "date-time",
    }
    assert s["properties"]["name"] == {"title": "Name", "type": "string"}
    assert s["properties"]["isMale"] == {
        "title": "Ismale",
        "default": True,
        "type": "boolean",
    }

    has_books = s["properties"]["hasBooks"]
    assert has_books
    assert has_books["title"] == "Hasbooks"
    assert has_books["uniqueItems"] == True
    assert has_books["type"] == "array"
    has_books_items = has_books["items"]
    assert has_books_items
    assert has_books_items["anyOf"]
    assert len(has_books_items["anyOf"]) == 3
    assert {
        "$ref": "#/definitions/Person_HasBooks_Book_RelatedItem"
    } in has_books_items["anyOf"]
    assert {
        "$ref": "#/definitions/Person_HasBooks_NonOwnableBook_RelatedItem"
    } in has_books_items["anyOf"]
    assert {
        "$ref": "#/definitions/Person_HasBooks_DefinitelyNonOwnableBook_RelatedItem"
    } in has_books_items["anyOf"]

    assert s["properties"]["ownsPets"] == {
        "title": "Ownspets",
        "uniqueItems": True,
        "type": "array",
        "items": {"$ref": "#/definitions/Person_OwnsPets_Pet_RelatedItem"},
    }

    owns_things = s["properties"]["ownsThings"]
    assert owns_things

    assert owns_things["title"] == "Ownsthings"
    assert owns_things["maxItems"] == 1
    assert owns_things["uniqueItems"] == True
    assert owns_things["type"] == "array"
    owns_things_items = owns_things["items"]
    assert owns_things_items
    assert len(owns_things_items["anyOf"]) == 2
    assert {
        "$ref": "#/definitions/Person_OwnsThings_Pet_RelatedItem"
    } in owns_things_items["anyOf"]
    assert {
        "$ref": "#/definitions/Person_OwnsThings_Book_RelatedItem"
    } in owns_things_items["anyOf"]

    has_root_vegetable = s["properties"]["hasRootVegetable"]
    assert has_root_vegetable
    assert has_root_vegetable["title"] == "Hasrootvegetable"
    assert has_root_vegetable["minItems"] == 1
    assert has_root_vegetable["maxItems"] == 1
    assert has_root_vegetable["uniqueItems"] == True
    assert has_root_vegetable["type"] == "array"
    has_root_vegetable_items = has_root_vegetable["items"]
    assert has_root_vegetable_items
    assert len(has_root_vegetable_items["anyOf"]) == 2
    assert {
        "$ref": "#/definitions/Person_HasRootVegetable_Potato_RelatedItem"
    } in has_root_vegetable_items["anyOf"]
    assert {
        "$ref": "#/definitions/Person_HasRootVegetable_Turnip_RelatedItem"
    } in has_root_vegetable_items["anyOf"]

    is_owner_of = s["properties"]["isOwnerOf"]
    assert is_owner_of
    assert is_owner_of["title"] == "Isownerof"
    assert is_owner_of["type"] == "array"
    is_owner_of_items = is_owner_of["items"]
    assert len(is_owner_of_items["anyOf"]) == 2
    assert {
        "$ref": "#/definitions/Person_IsOwnerOf_Pet_RelatedItem"
    } in is_owner_of_items["anyOf"]
    assert {
        "$ref": "#/definitions/Person_IsOwnerOf_Book_RelatedItem"
    } in is_owner_of_items["anyOf"]

    assert s["properties"]["isMemberOf"] == {
        "title": "Ismemberof",
        "type": "array",
        "items": {"$ref": "#/definitions/Person_IsMemberOf_Organisation_RelatedItem"},
    }

    assert s["properties"]["isIdentifiedBy"] == {
        "title": "Isidentifiedby",
        "type": "array",
        "items": {
            "$ref": "#/definitions/Person_IsIdentifiedBy_PersonIdentification_RelatedItem"
        },
    }

    is_author_of = s["properties"]["isAuthorOf"]
    assert is_author_of
    assert is_author_of["title"] == "Isauthorof"
    assert is_author_of["type"] == "array"
    is_author_of_items = is_author_of["items"]
    assert is_author_of_items
    assert len(is_author_of_items["anyOf"]) == 3
    assert {
        "$ref": "#/definitions/Person_IsAuthorOf_Book_RelatedItem"
    } in is_author_of_items["anyOf"]

    assert s["properties"]["isInvolvedInHappening"] == {
        "title": "Isinvolvedinhappening",
        "type": "array",
        "items": {
            "$ref": "#/definitions/Person_IsInvolvedInHappening_Happening_RelatedItem"
        },
    }

    assert s["required"] == [
        "uid",
        "lastDependentChange",
        "hasBooks",
        "ownsPets",
        "ownsThings",
        "hasRootVegetable",
        "dateOfBirth",
    ]

    assert s["definitions"] == {
        "Person_HasBooks_Book_RelatedItem": {
            "title": "Person_HasBooks_Book_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "book",
                    "enum": ["book"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_HasBooks_NonOwnableBook_RelatedItem": {
            "title": "Person_HasBooks_NonOwnableBook_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "nonownablebook",
                    "enum": ["nonownablebook"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_HasBooks_DefinitelyNonOwnableBook_RelatedItem": {
            "title": "Person_HasBooks_DefinitelyNonOwnableBook_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "definitelynonownablebook",
                    "enum": ["definitelynonownablebook"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_OwnsPets_Pet_RelatedItem_RelationData": {
            "title": "Person_OwnsPets_Pet_RelatedItem_RelationData",
            "type": "object",
            "properties": {
                "purchasedWhen": {"title": "Purchasedwhen", "type": "string"}
            },
        },
        "Person_OwnsPets_Pet_RelatedItem": {
            "title": "Person_OwnsPets_Pet_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "pet",
                    "enum": ["pet"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
                "relationData": {
                    "$ref": "#/definitions/Person_OwnsPets_Pet_RelatedItem_RelationData"
                },
            },
            "required": ["label", "uid", "relationData"],
        },
        "Person_OwnsThings_Pet_RelatedItem": {
            "title": "Person_OwnsThings_Pet_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "pet",
                    "enum": ["pet"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_OwnsThings_Book_RelatedItem": {
            "title": "Person_OwnsThings_Book_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "book",
                    "enum": ["book"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_HasRootVegetable_Potato_RelatedItem": {
            "title": "Person_HasRootVegetable_Potato_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "potato",
                    "enum": ["potato"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_HasRootVegetable_Turnip_RelatedItem": {
            "title": "Person_HasRootVegetable_Turnip_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "turnip",
                    "enum": ["turnip"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "DateImprecise_CalendarFormat_Calendar_RelatedItem": {
            "title": "DateImprecise_CalendarFormat_Calendar_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
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
                "realType": {
                    "title": "Realtype",
                    "default": "dateimprecise",
                    "enum": ["dateimprecise"],
                    "type": "string",
                },
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
                "date": {"title": "Date", "type": "string"},
                "calendarFormat": {
                    "title": "Calendarformat",
                    "uniqueItems": True,
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/DateImprecise_CalendarFormat_Calendar_RelatedItem"
                    },
                },
            },
            "required": ["uid", "calendarFormat"],
        },
        "DatePrecise_CalendarFormat_Calendar_RelatedItem": {
            "title": "DatePrecise_CalendarFormat_Calendar_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
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
                "realType": {
                    "title": "Realtype",
                    "default": "dateprecise",
                    "enum": ["dateprecise"],
                    "type": "string",
                },
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
                "date": {"title": "Date", "type": "string"},
                "calendarFormat": {
                    "title": "Calendarformat",
                    "uniqueItems": True,
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/DatePrecise_CalendarFormat_Calendar_RelatedItem"
                    },
                },
            },
            "required": ["uid", "calendarFormat"],
        },
        "Person_IsOwnerOf_Pet_RelatedItem": {
            "title": "Person_IsOwnerOf_Pet_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "pet",
                    "enum": ["pet"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_IsOwnerOf_Book_RelatedItem": {
            "title": "Person_IsOwnerOf_Book_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "book",
                    "enum": ["book"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_IsMemberOf_Organisation_RelatedItem": {
            "title": "Person_IsMemberOf_Organisation_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "organisation",
                    "enum": ["organisation"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_IsIdentifiedBy_PersonIdentification_RelatedItem": {
            "title": "Person_IsIdentifiedBy_PersonIdentification_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "personidentification",
                    "enum": ["personidentification"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_IsAuthorOf_Book_RelatedItem": {
            "title": "Person_IsAuthorOf_Book_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "book",
                    "enum": ["book"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_IsAuthorOf_NonOwnableBook_RelatedItem": {
            "title": "Person_IsAuthorOf_NonOwnableBook_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "nonownablebook",
                    "enum": ["nonownablebook"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_IsAuthorOf_DefinitelyNonOwnableBook_RelatedItem": {
            "title": "Person_IsAuthorOf_DefinitelyNonOwnableBook_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "definitelynonownablebook",
                    "enum": ["definitelynonownablebook"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_IsInvolvedInHappening_Happening_RelatedItem": {
            "title": "Person_IsInvolvedInHappening_Happening_RelatedItem",
            "type": "object",
            "properties": {
                "realType": {
                    "title": "Realtype",
                    "default": "happening",
                    "enum": ["happening"],
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
        "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
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
                    {"$ref": "#/definitions/Person_HasBooks_Book_RelatedItem"},
                    {
                        "$ref": "#/definitions/Person_HasBooks_NonOwnableBook_RelatedItem"
                    },
                    {
                        "$ref": "#/definitions/Person_HasBooks_DefinitelyNonOwnableBook_RelatedItem"
                    },
                ]
            },
        },
        "owns_pets": {
            "title": "Owns Pets",
            "uniqueItems": True,
            "type": "array",
            "items": {"$ref": "#/definitions/Person_OwnsPets_Pet_RelatedItem"},
        },
        "owns_things": {
            "title": "Owns Things",
            "maxItems": 1,
            "uniqueItems": True,
            "type": "array",
            "items": {
                "anyOf": [
                    {"$ref": "#/definitions/Person_OwnsThings_Pet_RelatedItem"},
                    {"$ref": "#/definitions/Person_OwnsThings_Book_RelatedItem"},
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
                    {
                        "$ref": "#/definitions/Person_HasRootVegetable_Potato_RelatedItem"
                    },
                    {
                        "$ref": "#/definitions/Person_HasRootVegetable_Turnip_RelatedItem"
                    },
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
                    {"$ref": "#/definitions/Person_IsOwnerOf_Pet_RelatedItem"},
                    {"$ref": "#/definitions/Person_IsOwnerOf_Book_RelatedItem"},
                ]
            },
        },
        "is_member_of": {
            "title": "Is Member Of",
            "type": "array",
            "items": {
                "$ref": "#/definitions/Person_IsMemberOf_Organisation_RelatedItem"
            },
        },
        "is_identified_by": {
            "title": "Is Identified By",
            "type": "array",
            "items": {
                "$ref": "#/definitions/Person_IsIdentifiedBy_PersonIdentification_RelatedItem"
            },
        },
        "is_author_of": {
            "title": "Is Author Of",
            "type": "array",
            "items": {
                "anyOf": [
                    {"$ref": "#/definitions/Person_IsAuthorOf_Book_RelatedItem"},
                    {
                        "$ref": "#/definitions/Person_IsAuthorOf_NonOwnableBook_RelatedItem"
                    },
                    {
                        "$ref": "#/definitions/Person_IsAuthorOf_DefinitelyNonOwnableBook_RelatedItem"
                    },
                ]
            },
        },
        "is_involved_in_happening": {
            "title": "Is Involved In Happening",
            "type": "array",
            "items": {
                "$ref": "#/definitions/Person_IsInvolvedInHappening_Happening_RelatedItem"
            },
        },
    },
    "required": [
        "uid",
        "last_dependent_change",
        "has_books",
        "owns_pets",
        "owns_things",
        "has_root_vegetable",
        "date_of_birth",
    ],
    "definitions": {
        "Person_HasBooks_Book_RelatedItem": {
            "title": "Person_HasBooks_Book_RelatedItem",
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
        "Person_HasBooks_NonOwnableBook_RelatedItem": {
            "title": "Person_HasBooks_NonOwnableBook_RelatedItem",
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
        "Person_HasBooks_DefinitelyNonOwnableBook_RelatedItem": {
            "title": "Person_HasBooks_DefinitelyNonOwnableBook_RelatedItem",
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
        "Person_OwnsPets_Pet_RelatedItem_RelationData": {
            "title": "Person_OwnsPets_Pet_RelatedItem_RelationData",
            "type": "object",
            "properties": {
                "purchased_when": {"title": "Purchased When", "type": "string"}
            },
        },
        "Person_OwnsPets_Pet_RelatedItem": {
            "title": "Person_OwnsPets_Pet_RelatedItem",
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
                    "$ref": "#/definitions/Person_OwnsPets_Pet_RelatedItem_RelationData"
                },
            },
            "required": ["label", "uid", "relation_data"],
        },
        "Person_OwnsThings_Pet_RelatedItem": {
            "title": "Person_OwnsThings_Pet_RelatedItem",
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
        "Person_OwnsThings_Book_RelatedItem": {
            "title": "Person_OwnsThings_Book_RelatedItem",
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
        "Person_HasRootVegetable_Potato_RelatedItem": {
            "title": "Person_HasRootVegetable_Potato_RelatedItem",
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
        "Person_HasRootVegetable_Turnip_RelatedItem": {
            "title": "Person_HasRootVegetable_Turnip_RelatedItem",
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
        "DateImprecise_CalendarFormat_Calendar_RelatedItem": {
            "title": "DateImprecise_CalendarFormat_Calendar_RelatedItem",
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
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
                "date": {"title": "Date", "type": "string"},
                "calendar_format": {
                    "title": "Calendar Format",
                    "uniqueItems": True,
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/DateImprecise_CalendarFormat_Calendar_RelatedItem"
                    },
                },
            },
            "required": ["uid", "calendar_format"],
        },
        "DatePrecise_CalendarFormat_Calendar_RelatedItem": {
            "title": "DatePrecise_CalendarFormat_Calendar_RelatedItem",
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
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
                "date": {"title": "Date", "type": "string"},
                "calendar_format": {
                    "title": "Calendar Format",
                    "uniqueItems": True,
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/DatePrecise_CalendarFormat_Calendar_RelatedItem"
                    },
                },
            },
            "required": ["uid", "calendar_format"],
        },
        "Person_IsOwnerOf_Pet_RelatedItem": {
            "title": "Person_IsOwnerOf_Pet_RelatedItem",
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
        "Person_IsOwnerOf_Book_RelatedItem": {
            "title": "Person_IsOwnerOf_Book_RelatedItem",
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
        "Person_IsMemberOf_Organisation_RelatedItem": {
            "title": "Person_IsMemberOf_Organisation_RelatedItem",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "organisation",
                    "enum": ["organisation"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_IsIdentifiedBy_PersonIdentification_RelatedItem": {
            "title": "Person_IsIdentifiedBy_PersonIdentification_RelatedItem",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "personidentification",
                    "enum": ["personidentification"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
        "Person_IsAuthorOf_Book_RelatedItem": {
            "title": "Person_IsAuthorOf_Book_RelatedItem",
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
        "Person_IsAuthorOf_NonOwnableBook_RelatedItem": {
            "title": "Person_IsAuthorOf_NonOwnableBook_RelatedItem",
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
        "Person_IsAuthorOf_DefinitelyNonOwnableBook_RelatedItem": {
            "title": "Person_IsAuthorOf_DefinitelyNonOwnableBook_RelatedItem",
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
        "Person_IsInvolvedInHappening_Happening_RelatedItem": {
            "title": "Person_IsInvolvedInHappening_Happening_RelatedItem",
            "type": "object",
            "properties": {
                "real_type": {
                    "title": "Real Type",
                    "default": "happening",
                    "enum": ["happening"],
                    "type": "string",
                },
                "label": {"title": "Label", "type": "string"},
                "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
            },
            "required": ["label", "uid"],
        },
    },
}
