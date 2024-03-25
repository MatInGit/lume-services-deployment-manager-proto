from prefect import flow, get_run_logger, tags, task
from mlflow import MlflowClient

@task 
def get_models():
    logger = get_run_logger()
    
    # list all registered models
    client = MlflowClient()#
    models = client.search_registered_models()
    for model in models:
        logger.info(f"Found model: {model.name}")
    
    return models

@task
def get_by_model_aliases(models):
    logger = get_run_logger()
    client = MlflowClient()
    
    for model in models:
        model_info = client.get_model_version_by_alias(model.name , "champion")
        logger.info(f"Found model champion: {model.name}")
        logger.info(f"Getting model champion for {model.name}")
        # print all model tags
        logger.info(f"Regsitered Model tags: {model.tags}")
        # experimnet tags
        logger.info(f"Experiment tags: {client.get_experiment_by_name(model.name).tags}")

@flow
def main_flow():
    logger = get_run_logger()
    models = get_models()
    get_by_model_aliases(models)
    
    
if __name__ == "__main__":
    with tags("local"):
        main_flow.run()
        