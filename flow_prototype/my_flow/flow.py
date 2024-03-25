from prefect import flow, get_run_logger, tags, task
from mlflow import MlflowClient

from utils.object import BaseWorkflow # base class for workflow 
from flow_utils.mlflow_flow import get_models, get_by_model_aliases # all mlflow related stuff


@flow
def main_flow():
    logger = get_run_logger()
    models = get_models()
    info_dicts = get_by_model_aliases(models)
    for info_dict in info_dicts:
        logger.info(f"Model info: {info_dict}")
        test_instance = BaseWorkflow(**info_dict)
        logger.info(f"Test instance: {test_instance}")


if __name__ == "__main__":
    with tags("local"):
        main_flow.run()
