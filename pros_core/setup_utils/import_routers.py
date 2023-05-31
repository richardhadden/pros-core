import inspect
from fastapi import FastAPI, APIRouter
from pydantic import BaseSettings


def import_routers(_app: FastAPI, settings: BaseSettings) -> FastAPI:
    """Import routers from app BaseSettings configuration"""

    for pros_app in settings.INSTALLED_APPS:
        try:
            module = __import__(f"{pros_app}.api.v1")
            router = inspect.getmembers(
                module.api.v1,
                lambda x: isinstance(x, APIRouter),
            )[0][1]
            _app.include_router(router)
        except Exception as e:
            pass
