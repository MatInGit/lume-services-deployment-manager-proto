import os
import mlflow
from mlflow.tracking import MlflowClient

from utils.object import BaseWorkflow

import logging
import json


def get_run_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


logger = get_run_logger()


json_data = json.load(open("cred.json"))

os.environ["MLFLOW_TRACKING_USERNAME"] = json_data["MLFLOW_TRACKING_USERNAME"]
os.environ["MLFLOW_TRACKING_PASSWORD"] = json_data["MLFLOW_TRACKING_PASSWORD"]
os.environ["MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"] = json_data[
    "MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"
]
os.environ["AWS_DEFAULT_REGION"] = json_data["AWS_DEFAULT_REGION"]
os.environ["AWS_REGION"] = json_data["AWS_REGION"]
os.environ["AWS_ACCESS_KEY_ID"] = json_data["AWS_ACCESS_KEY_ID"]
os.environ["AWS_SECRET_ACCESS_KEY"] = json_data["AWS_SECRET_ACCESS_KEY"]
os.environ["MLFLOW_S3_ENDPOINT_URL"] = json_data["MLFLOW_S3_ENDPOINT_URL"]
# tracking uri
os.environ["MLFLOW_TRACKING_URI"] = json_data["MLFLOW_TRACKING_URI"]


def get_models(logger=logger):
    # list all registered models
    client = MlflowClient()  #
    models = client.search_registered_models()
    for model in models:
        logger.info(f"Found model: {model.name}")

    return models


def get_by_model_aliases(models, logger=logger):
    client = MlflowClient()

    for model in models:
        model_info = client.get_model_version_by_alias(model.name, "champion")
        # logger.info(f"Found model champion: {model.name}")
        # logger.info(f"Getting model champion for {model.name}")
        # # print all model tags
        # logger.info(f"Regsitered Model tags: {model.tags}")
        # # experimnet tags
        # logger.info(f"Experiment tags: {model_info.tags}")

        logger.info(f"Model: {model.name}")
        try:
            model_instance = BaseWorkflow(
                workflow_model_name=model.name,
                workflow_model_version=model_info.version,
                maintainer=None,
                deplyment_status=None,
                **model.tags,
            )
            logger.info(f"Model: {model_instance}")
        except Exception as e:
            logger.error(f"Error: {e}")

        combined_dict = {**model.tags}
        print(combined_dict)


def main_flow():
    models = get_models()
    get_by_model_aliases(models)


if __name__ == "__main__":
    main_flow()
