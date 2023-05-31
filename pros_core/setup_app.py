from fastapi import FastAPI
from pros_core.setup_utils import (
    build_routes,
    import_models,
    import_routers,
    setup_model_manager,
)
from pydantic import BaseSettings


def setup_app(_app: FastAPI, settings: BaseSettings) -> FastAPI:
    import_routers(_app, settings)
    models = import_models(settings)
    setup_model_manager(models)
    build_routes(_app, models)
    return _app