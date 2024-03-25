import os 
import mlflow
from mlflow.tracking import MlflowClient 
import logging

def get_run_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

logger = get_run_logger()

# dont do this in production
os.environ["MLFLOW_TRACKING_USERNAME"] = "admin"
os.environ["MLFLOW_TRACKING_PASSWORD"] = "password"
os.environ["MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"] = "true"
os.environ["AWS_DEFAULT_REGION"] = "eu-west-3"
os.environ["AWS_REGION"] = "eu-west-3"
os.environ["AWS_ACCESS_KEY_ID"] = "admin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test_password"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://172.24.5.222:9020"
# tracking uri
os.environ["MLFLOW_TRACKING_URI"] = "https://ard-mlflow.slac.stanford.edu"



def get_models():
    # list all registered models
    client = MlflowClient()#
    models = client.search_registered_models()
    for model in models:
        logger.info(f"Found model: {model.name}")
    
    return models


def get_by_model_aliases(models):
    client = MlflowClient()
    
    for model in models:
        model_info = client.get_model_version_by_alias(model.name , "champion")
        logger.info(f"Found model champion: {model.name}")
        logger.info(f"Getting model champion for {model.name}")
        # print all model tags
        logger.info(f"Regsitered Model tags: {model.tags}")
        # experimnet tags
        logger.info(f"Experiment tags: {model_info}")


def main_flow():
    models = get_models()
    get_by_model_aliases(models)
    
    
if __name__ == "__main__":
    main_flow()
        