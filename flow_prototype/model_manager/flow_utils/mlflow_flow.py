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

        try:    
            # logger.info(f"Model type: {type(model)}")
            if type(model) == str:
                model_name = model
                model = client.get_registered_model(model_name)
            else: # needs to be elif type(model) == whatever the type is for mlflow model
                model_name = model.name

            model_info = client.get_model_version_by_alias(model_name, "champion")
            logger.info(f"Model: {model_name}")
            combined_dict = {**model.tags}
            logger.info(f"Tags: {combined_dict}")
            combined_dict["workflow_model_name"] = model_name
            combined_dict["workflow_model_version"] = model_info.version
            model_info_dicts.append(combined_dict)
        except Exception as e:
            logger.warning(
                f"Workflow instance could not be created. Check model tags for {model_name}"
            )
            logger.warning(f"Error: {e}")
            continue
    return model_info_dicts


def set_registered_model_tag(model_name, tag_key, tag_value):
    client = MlflowClient()
    client.set_registered_model_tag(model_name, tag_key, tag_value)
