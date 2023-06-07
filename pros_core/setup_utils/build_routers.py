from fastapi import APIRouter


def build_routes(_app, models, ModelManager):
    router = APIRouter()
    for app_model in ModelManager.models:

        def get() -> list[app_model.pydantic_return_model]:
            return [
                {
                    "uid": "550e8400-e29b-41d4-a716-446655440000",
                    "real_type": "animal",
                    "label": "string",
                    "created_by": "string",
                    "created_when": "2023-06-07T10:18:45.871Z",
                    "modified_by": "string",
                    "modified_when": "2023-06-07T10:18:45.871Z",
                    "is_deleted": False,
                    "last_dependent_change": "2023-06-07T10:18:45.871Z",
                    "is_involved_in_happening": [
                        {
                            "real_type": "animal",
                            "label": "string",
                            "uid": "550e8400-e29b-41d4-a716-446655440001",
                        }
                    ],
                }
            ]

        router.add_api_route("/" + app_model.model_name.lower(), endpoint=get)
    _app.include_router(router)
