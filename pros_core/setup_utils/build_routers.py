from fastapi import APIRouter


def build_routes(_app, models):
    router = APIRouter()
    for app_name, model_name, model in models:

        def get():
            return f"GETTING {model_name}"

        router.add_api_route("/" + model_name.lower(), endpoint=get)
    _app.include_router(router)
