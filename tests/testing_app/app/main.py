import inspect

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings

from pros_core.setup_app import setup_app


map(__import__, settings.INSTALLED_APPS)


def get_application():
    _app = FastAPI(title=settings.PROJECT_NAME)
    _app = setup_app(_app, settings)
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return _app


app = get_application()
