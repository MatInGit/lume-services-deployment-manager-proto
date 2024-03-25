from prefect import flow, get_run_logger, tags, task
from mlflow import MlflowClient

# prefect kubernetes flow
from prefect import flow
from prefect.blocks.kubernetes import KubernetesClusterConfig
from prefect_kubernetes.credentials import KubernetesCredentials
from prefect_kubernetes.jobs import list_namespaced_job

from utils.object import BaseWorkflow # base class for workflow 
from flow_utils.mlflow_flow import get_models, get_by_model_aliases # all mlflow related stuff

# k8s_config = KubernetesClusterConfig.from_file('~/.kube/config')
# k8s_credentials = KubernetesCredentials(cluster_config=k8s_config)

@task
def kubernetes_orchestrator():
    v1_job_list = list_namespaced_job(
        kubernetes_credentials=k8s_credentials,
        namespace="prefect",
    )
    return v1_job_list


@flow
def main_flow():
    logger = get_run_logger()
    models = get_models()
    info_dicts = get_by_model_aliases(models)
    for info_dict in info_dicts:
        logger.info(f"Model info: {info_dict}")
        workflow_instance = BaseWorkflow(**info_dict)
        
        if workflow_instance.deployment_type == "continuous":
            logger.info(f"Deploying {workflow_instance.workflow_model_name} with handler {workflow_instance.deployment_handler_type}")
            logger.info("... deploying to k8s cluster (not really but that's the idea) ... ")
            # pseudo-code/prototoype section 
            # handler = get_handler(workflow_instance.deployment_handler_type)
            # handler.deploy(workflow_instance)
        elif workflow_instance.deployment_type == "batch":
            logger.info(f"Deploying {workflow_instance.workflow_model_name} with handler {workflow_instance.deployment_handler_type}")
            logger.info("... running batch job (eventually) ... ")
            # pseudo-code/prototoype section 
            # start mlfow batch job
        else:   
            logger.error(f"Invalid deployment type {workflow_instance.deployment_type} for model {workflow_instance.workflow_model_name}")
        
if __name__ == "__main__":
    with tags("local"):
        main_flow.run()
