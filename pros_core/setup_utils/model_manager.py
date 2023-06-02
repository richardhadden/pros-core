from camel_converter import to_pascal
from pros_core.models import BaseNode
from pros_core.setup_utils.build_app_model_definitions import (
    AppModel,
    ModelManager,
    ModelManagerClass,
    ModelManagerException,
    build_child_nodes,
    build_parent_classes_set,
    build_properties,
    build_related_reifications,
    build_relationships,
    build_reverse_relationships,
    build_subclasses_hierarchy,
    build_subclasses_set,
)


def create_app_model(
    app_name: str, model_class: type[BaseNode], model_name: str, _mm: ModelManagerClass
) -> AppModel:
    return AppModel(
        app_name=to_pascal(app_name),
        model_class=model_class,
        model_name=model_name,
        properties=build_properties(model=model_class),
        relationships=build_relationships(model=model_class),
        child_nodes=build_child_nodes(model=model_class),
        related_reifications=build_related_reifications(model=model_class),
        subclass_hierarchy=build_subclasses_hierarchy(model=model_class),
        subclasses=build_subclasses_set(model=model_class),
        parent_classes=build_parent_classes_set(model=model_class),
        reverse_relationships=build_reverse_relationships(model=model_class),
        meta=model_class._meta,
        _mm=_mm,
    )


def setup_model_manager(pros_models: list[tuple[str, type[BaseNode]]]) -> None:
    for app_name, model_name, model in pros_models:
        # Check if it's a class defined in this model (not imported from somewhere)
        # and that it's a top-level node

        # Create AppModel for each model and add to ModelManager
        app_model = create_app_model(
            app_name=app_name,
            model_class=model,
            model_name=model_name,
            _mm=ModelManager,
        )
        ModelManager.add_model(app_model)

        # And sling the app_model onto the model itself for good measure
        model._app_model: AppModel = app_model
