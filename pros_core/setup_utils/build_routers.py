from typing import Optional

from fastapi import APIRouter, Query


def build_routes(_app, models, ModelManager):
    router = APIRouter()
    for app_model in ModelManager.models:

        async def get(
            q: Optional[str] = Query(
                None, description="Filter parameter for autocomplete query"
            )
        ) -> list[app_model.pydantic_return_model]:
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
                            "real_type": "happening",
                            "label": "string",
                            "uid": "550e8400-e29b-41d4-a716-446655440001",
                        }
                    ],
                }
            ]

        router.add_api_route(
            "/entities/" + app_model.model_name.lower() + "/",
            endpoint=get,
            name=f"{app_model.model_name}.list",
        )
    _app.include_router(router)
