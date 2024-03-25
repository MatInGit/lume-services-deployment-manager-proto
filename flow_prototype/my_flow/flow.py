from prefect import flow, get_run_logger, tags, task
from mlflow import MlflowClient

# prefect kubernetes flow
from prefect import flow
from prefect.blocks.kubernetes import KubernetesClusterConfig
from prefect_kubernetes.credentials import KubernetesCredentials
from prefect_kubernetes.jobs import list_namespaced_job

from utils.object import BaseWorkflow  # base class for workflow
from flow_utils.mlflow_flow import (
    get_models,
    get_by_model_aliases,
    set_registered_model_tag,
)  # all mlflow related stuff

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
    model_dicts = get_by_model_aliases(models)
    for model_dict in model_dicts:
        logger.info(f"Model info: {model_dict}")
        workflow_instance = BaseWorkflow(**model_dict)

        if workflow_instance.deployment_type == "continuous":
            logger.info(
                f"Deploying {workflow_instance.workflow_model_name} with handler {workflow_instance.deployment_handler_type}"
            )
            logger.info(
                "... deploying to k8s cluster (not really but that's the idea) ... "
            )
            # handler = get_handler_by_falvor(workflow_instance.deployment_handler_type)
            # handler.deploy(workflow_instance) # spins up a k8s pod with the model
            # pod_name = handler.get_pod_name(workflow_instance)
            set_registered_model_tag(
                workflow_instance.workflow_model_name,
                "deployment_status",
                "deployed",
            )
            # pretend pod name
            pod_name = "model-pod-1234"
            logger.info(f"Model deployed to pod {pod_name}")
            set_registered_model_tag(
                workflow_instance.workflow_model_name,
                "deployment_pod_name",
                pod_name,
            )
            
        elif workflow_instance.deployment_type == "batch":
            logger.info(
                f"Deploying {workflow_instance.workflow_model_name} with handler {workflow_instance.deployment_handler_type}"
            )
            logger.info("... running batch job (eventually) ... ")
            # exectute get data 
            # execute model with data
            # save results to user specified location
            
        else:
            logger.error(
                f"Invalid deployment type {workflow_instance.deployment_type} for model {workflow_instance.workflow_model_name}"
            )


if __name__ == "__main__":
    with tags("local"):
        main_flow.run()
