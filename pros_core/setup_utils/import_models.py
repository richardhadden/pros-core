import inspect

from pros_core.models import BaseNode
from pydantic import BaseSettings


def import_models(settings: BaseSettings) -> list[tuple[str, str, type[BaseNode]]]:
    """Import models from app BaseSettings configuration"""

    all_models = []
    for pros_app in settings.INSTALLED_APPS:
        module = __import__(f"{pros_app}.models")
        models = inspect.getmembers(
            module.models,
            lambda x: inspect.isclass(x)
            and issubclass(x, BaseNode)
            and x.__name__
            not in {
                "BaseNode",
                "AbstractNode",
                "AbstractReification",
                "ChildNode",
                "AbstractTrait",
            },
        )
        models = [(pros_app, model[0], model[1]) for model in models]
        all_models += models
    return all_models
