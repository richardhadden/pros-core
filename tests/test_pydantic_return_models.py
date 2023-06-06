from typing import Union, get_args, get_origin, get_type_hints

import pydantic
import pytest
from pros_core.setup_app import setup_app
from testing_app.app.core.config import settings
from testing_app.app.main import app


@pytest.fixture(scope="module")
def setup_app():
    setup_app(app, settings)


def test_build_pydantic_return_child_nodes():
    from pros_core.setup_utils.build_pydantic_return_models import (
        build_pydantic_return_child_nodes,
    )
    from test_app.models import Person

    types = build_pydantic_return_child_nodes(Person)
    assert types["date_of_birth"]

    assert tuple(t.__name__ for t in get_args(types["date_of_birth"][0])) == ("Union",)
    assert (
        str(types["date_of_birth"][0])
        == "list[typing.Union[pydantic.main.DateImprecise, pydantic.main.DatePrecise]]"
    )


def test_build_pydantic_model_for_person():
    from pros_core.setup_utils.build_pydantic_return_models import (
        build_pydantic_return_model,
        build_relation_return_model,
    )
    from test_app.models import Calendar, Person

    PydanticPerson = build_pydantic_return_model(Person)
    """
    assert PydanticPerson.schema() == {
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
                "type": "array",
                "items": {"$ref": "#/definitions/BookRelated"},
            },
            "owns_pets": {
                "title": "Owns Pets",
                "type": "array",
                "items": {"$ref": "#/definitions/PetRelated"},
            },
            "date_of_birth": {
                "title": "Date Of Birth",
                "type": "array",
                "items": {
                    "anyOf": [
                        {"$ref": "#/definitions/DateImprecise"},
                        {"$ref": "#/definitions/DatePrecise"},
                    ]
                },
            },
        },
        "required": [
            "last_dependent_change",
            "has_books",
            "owns_pets",
            "date_of_birth",
        ],
        "definitions": {
            "BookRelated": {
                "title": "BookRelated",
                "type": "object",
                "properties": {
                    "real_type": {"title": "Real Type", "default": "book"},
                    "label": {"title": "Label", "type": "string"},
                    "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
                    "relation_data": {"title": "Relation Data", "type": "object"},
                },
                "required": ["label", "uid", "relation_data"],
            },
            "PetRelated": {
                "title": "PetRelated",
                "type": "object",
                "properties": {
                    "real_type": {"title": "Real Type", "default": "pet"},
                    "label": {"title": "Label", "type": "string"},
                    "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
                    "relation_data": {"title": "Relation Data", "type": "object"},
                },
                "required": ["label", "uid", "relation_data"],
            },
            "CalendarRelated": {
                "title": "CalendarRelated",
                "type": "object",
                "properties": {
                    "real_type": {"title": "Real Type", "default": "calendar"},
                    "label": {"title": "Label", "type": "string"},
                    "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
                    "relation_data": {"title": "Relation Data", "type": "object"},
                },
                "required": ["label", "uid", "relation_data"],
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
                        "type": "array",
                        "items": {"$ref": "#/definitions/CalendarRelated"},
                    },
                },
                "required": ["calendar_format"],
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
                        "type": "array",
                        "items": {"$ref": "#/definitions/CalendarRelated"},
                    },
                },
                "required": ["calendar_format"],
            },
        },
    }"""
