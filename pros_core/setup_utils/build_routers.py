from typing import Optional

from fastapi import APIRouter, Depends, Query
from pros_core.auth import LoggedInUser


def build_routes(_app, models, ModelManager):
    router = APIRouter()
    for app_model in ModelManager.models:

        async def get_list(
            user=LoggedInUser,
            q: Optional[str] = Query(
                None, description="Filter parameter for autocomplete query"
            ),
        ) -> list[app_model.pydantic_return_model]:
            return [
                {
                    "uid": "550e8400-e29b-41d4-a716-446655440000",
                    "real_type": "animal",
                    "label": "Mister Gorilla",
                    "created_by": "rhadden",
                    "created_when": "2023-06-07T10:18:45.871Z",
                    "modified_by": "rhadden",
                    "modified_when": "2023-06-07T10:18:45.871Z",
                    "is_deleted": False,
                    "last_dependent_change": "2023-06-07T10:18:45.871Z",
                    "is_involved_in_happening": [
                        {
                            "real_type": "happening",
                            "label": "The Gorilla's Gathering",
                            "uid": "550e8400-e29b-41d4-a716-446655440001",
                        }
                    ],
                }
            ]

        router.add_api_route(
            "/entities/" + app_model.model_name.lower() + "/",
            endpoint=get_list,
            name=f"{app_model.model_name}.list",
        )

        # TODO: remove this at some stage when there's real data, and we can protect actual routes
        @_app.get("/protected/")
        def protected(user=LoggedInUser) -> str:
            return "Got a protected thing"

    _app.include_router(router)
