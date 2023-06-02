from typing import Union, get_args, get_origin, get_type_hints

import pydantic


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
    )
    from test_app.models import Person

    assert build_pydantic_return_model(Person).schema() == {
        "title": "Person",
        "type": "object",
        "properties": {
            "real_type": {
                "default": "person",
                "allOf": [{"$ref": "#/definitions/RealType"}],
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
                "items": {"$ref": "#/definitions/Book"},
            },
            "owns_pets": {
                "title": "Owns Pets",
                "type": "array",
                "items": {"$ref": "#/definitions/Pet"},
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
            "RealType": {
                "title": "RealType",
                "description": "An enumeration.",
                "enum": ["person"],
                "type": "string",
            },
            "Book": {
                "title": "Book",
                "type": "object",
                "properties": {
                    "real_type": {"title": "Real Type", "default": "book"},
                    "label": {"title": "Label", "type": "string"},
                    "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
                    "relation_data": {"title": "Relation Data", "type": "object"},
                },
                "required": ["label", "uid", "relation_data"],
            },
            "Pet": {
                "title": "Pet",
                "type": "object",
                "properties": {
                    "real_type": {"title": "Real Type", "default": "pet"},
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
                    "real_type": {"title": "Real Type", "default": "dateimprecise"},
                    "label": {"title": "Label", "type": "string"},
                    "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
                    "relation_data": {"title": "Relation Data", "type": "object"},
                },
                "required": ["label", "uid", "relation_data"],
            },
            "DatePrecise": {
                "title": "DatePrecise",
                "type": "object",
                "properties": {
                    "real_type": {"title": "Real Type", "default": "dateprecise"},
                    "label": {"title": "Label", "type": "string"},
                    "uid": {"title": "Uid", "type": "string", "format": "uuid4"},
                    "relation_data": {"title": "Relation Data", "type": "object"},
                },
                "required": ["label", "uid", "relation_data"],
            },
        },
    }
