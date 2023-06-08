from fastapi import FastAPI
from pros_core.auth import build_auth
from pros_core.setup_utils import (
    ModelManager,
    build_routes,
    import_models,
    import_routers,
    import_traits,
    setup_model_manager,
)
from pydantic import BaseSettings


def setup_app(_app: FastAPI, settings: BaseSettings) -> FastAPI:
    import_routers(_app, settings)
    models = import_models(settings)
    traits = import_traits(settings)
    setup_model_manager(models, traits)
    build_routes(_app, models, ModelManager)
    build_auth(_app)
    return _app
