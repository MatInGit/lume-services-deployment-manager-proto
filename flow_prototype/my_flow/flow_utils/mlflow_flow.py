from prefect import flow, get_run_logger, tags, task
from mlflow import MlflowClient


@task
def get_models():
    # list all registered models
    logger = get_run_logger()
    client = MlflowClient()  #
    models = client.search_registered_models()
    for model in models:
        logger.info(f"Found model: {model.name}")

    return models


@task
def get_by_model_aliases(models):
    client = MlflowClient()
    logger = get_run_logger()
    model_info_dicts = []
    for model in models:

        model_info = client.get_model_version_by_alias(model.name, "champion")
        logger.info(f"Model: {model.name}")

        combined_dict = {**model.tags}
        combined_dict["workflow_model_name"] = model.name
        combined_dict["workflow_model_version"] = model_info.version
        combined_dict["maintainer"] = None
        combined_dict["deplyment_status"] = None
        combined_dict["deployment_handler_type"] = "MLflow:pyfunc"

        model_info_dicts.append(combined_dict)

    return model_info_dicts

@task
def set_registered_model_tag(model_name, tag_key, tag_value):
    client = MlflowClient()
    client.set_registered_model_tag(model_name, tag_key, tag_value)