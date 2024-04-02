from prefect import flow, get_run_logger, tags, task
import random
from prefect.blocks.kubernetes import KubernetesClusterConfig
from prefect_kubernetes.credentials import KubernetesCredentials
from prefect_kubernetes.jobs import list_namespaced_job

from model_utils.workflow_base import BaseWorkflow  # base class for workflow
from flow_utils.mlflow_flow import (
    get_models,
    get_by_model_aliases,
    set_registered_model_tag,
)  # all mlflow related stuff

kubernetes_credentials = (
    KubernetesCredentials()
)  # Create an instance of KubernetesCredentials


@task
def process_instance(workflow_instance: BaseWorkflow):
    logger = get_run_logger()
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
        pod_name = f"model-pod-{random.randint(1, 1000)}"
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


@flow
def model_manager():
    logger = get_run_logger()
    namespaced_job_list = list_namespaced_job(
        namespace="prefect",
        kubernetes_credentials=kubernetes_credentials,
    )
    logger.info(f"Found {len(namespaced_job_list)} jobs in namespace my-namespace")
    for job in namespaced_job_list:
        logger.info(f"Job: {job.metadata.name}")
    models = get_models()
    model_dicts = get_by_model_aliases(models)
    for model_dict in model_dicts:
        try:
            workflow_instance = BaseWorkflow(**model_dict)
            process_instance.submit(workflow_instance)
        except Exception as e:
            logger.error(f"Error: {e}")
            raise e


if __name__ == "__main__":
    with tags("local"):
        model_manager.run()
