from camel_converter import to_pascal
from pros_core.models import AbstractTrait, BaseNode
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
from pros_core.setup_utils.build_pydantic_return_models import (
    build_pydantic_return_model,
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


def setup_model_manager(
    pros_models: list[tuple[str, str, type[BaseNode]]],
    pros_traits: list[tuple[str, str, type[AbstractTrait]]],
) -> None:
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

    for app_name, trait_name, trait in pros_traits:
        app_model = create_app_model(
            app_name=app_name,
            model_class=trait,
            model_name=trait_name,
            _mm=ModelManager,
        )
        ModelManager.add_model(app_model)

        model._app_model: AppModel = app_model

    for app_model in ModelManager.models:
        pydantic_return_model = (
            build_pydantic_return_model(neomodel_class=app_model.model_class),
        )

        # TODO: heaven knows why this is a tuple not just the class... seems most improbable
        # and can't find the error... attempt to figure that out!
        app_model.pydantic_return_model = pydantic_return_model[0]
